import json
from dataclasses import asdict

from util import swagger
from util.format import portal_template, jinja_template
from util.auth import require_access
from util.session import current_session
from objs.user import User, get_users_with_lab, filter_lab_access
from util.responses import wrap_response, form_body_to_dict, json_body_to_dict
from util.labs import LAB_CONFIGS
from objs.lab import Lab
from util.exceptions import MalformedRequest
from util.dynamo_db import dynamo_filter, get_all_items
from util.manage_access import (
    validate_edit_user_request,
    validate_delete_lab_access,
    validate_set_lab_access,
)

from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools import Logger

logger = Logger(child=True)

access_router = Router()

access_route = {
    "router": access_router,
    "prefix": "/portal/access",
    "name": "Access",
}


# This catches "/portal/access" (this routers 'root'):
@access_router.get("", include_in_schema=False)
@require_access("admin", human=True)
@portal_template()
def access_root() -> str:
    # Filter for NEW and PENDING requests
    filters_is = dynamo_filter(
        attr_name="status", filter_value=["new", "pending"], filter_action="in"
    )
    requests = get_all_items(table_id="request", limit=200, filters=filters_is)

    template_input = {"requests": requests}

    logger.info(f"template_input = {template_input}")

    return jinja_template(template_input, "manage_access.j2")


@access_router.get("/manage/<shortname>/requests/", include_in_schema=False)
@require_access("admin", human=True)
@portal_template()
def list_access_requests(shortname):
    lab = Lab(labname=shortname)
    template_input = {"requests": lab.get_requests()}
    return jinja_template(template_input, "manage_access.j2")


@access_router.get(
    "/manage/<shortname>/raw_request/<username>/", include_in_schema=False
)
@require_access("admin", human=True)
def get_raw_access_request(shortname, username):
    lab = Lab(labname=shortname)
    request_data = lab.get_access_request(username)
    return wrap_response(
        body=json.dumps(request_data),
        code=200 if request_data else 422,
        content_type=content_types.APPLICATION_JSON,
    )


@access_router.get("/manage/<shortname>", include_in_schema=False)
@require_access("admin", human=True)
@portal_template()
def manage_lab(shortname):
    template_input = {}

    user_filter = access_router.current_event.query_string_parameters.get("user_filter")
    row_limit = 200

    # Get users of lab, check if lab exists
    users = get_users_with_lab(
        shortname,
        limit=row_limit,
        username_filter=user_filter,
    )
    users = sorted(users, key=lambda x: x["username"])
    template_input["users"] = users

    lab = LAB_CONFIGS[shortname]
    template_input["lab"] = lab
    template_input["allows_requests"] = len(lab.application_questions) > 0
    template_input["rowcount"] = len(users)
    template_input["exceeded"] = len(users) >= row_limit

    return jinja_template(template_input, "manage.j2")


@access_router.post("/manage/<shortname>/edituser", include_in_schema=False)
@require_access("admin", human=True)
def edit_user(shortname):
    # Grab the username of the user making the request
    admin_username = current_session.auth.cognito.username
    # Parse request
    body = access_router.current_event.body

    if body is None:
        error = "Body not provided to edit_user"
        logger.error(error)
        raise MalformedRequest(error)
    body = form_body_to_dict(body)

    # Validate request
    success, message = validate_edit_user_request(body=body)
    if not success:
        logger.error(message)
        raise MalformedRequest(message)

    # Edit user
    user = User(body["username"])

    if body["action"] == "add_user":
        user.add_lab(
            lab_short_name=shortname,
            lab_profiles=[s.strip() for s in body["lab_profiles"].split(",")],
            time_quota=body["time_quota"].strip() or None,
            lab_country_status=body["lab_country_status"],
        )
        logger.info(f'{admin_username} added user "{body["username"]}" to {shortname}')

    elif body["action"] == "remove_user":
        user.remove_lab(shortname)
        logger.info(
            f'{admin_username} removed user "{body["username"]}" from {shortname}'
        )

    else:
        error = f"Invalid edit_user action {body['action']}"
        logger.error(error)
        raise MalformedRequest(error)

    # Send the user to the management page
    next_url = f"/portal/access/manage/{shortname}"
    return wrap_response(
        body={f"Redirect to {next_url}"},
        code=302,
        headers={"Location": next_url},
    )


@access_router.get(
    "/labs/<username>",
    description="Returns a list of all labs a user has access to.",
    response_description="A dict containing a list of labs the user has access to.",
    responses={
        **swagger.format_response(
            example={
                "labs": [
                    {
                        "<lab_name>": {
                            "lab_profiles": ["profile1", "profile2"],
                            "can_user_access_lab": True,
                            "can_user_see_lab_card": False,
                            "time_quota": "1h",
                            "lab_country_status": "active",
                        },
                    },
                ],
                "message": "OK",
            },
            description="Returns a list of labs the user has access to.",
            code=200,
        ),
        **swagger.code_403,
        **swagger.code_404_user_not_found,
    },
    tags=[access_route["name"]],
)
@require_access("admin", human=False)
def get_user_labs(username):
    # Find user in db
    user = User(username=username, create_if_missing=False)

    # Should this return the users filtered labs (including viewable and accessable)
    # Or should it just return the labs the user has access to
    lab_access: dict = filter_lab_access(user)
    lab_access["viewable_labs_config"] = {
        labname: asdict(lab_access["viewable_labs_config"][labname])
        for labname in lab_access["viewable_labs_config"]
    }

    # Return user labs
    return wrap_response(
        body=json.dumps(
            {
                "labs": lab_access,
                "message": "OK",
            }
        ),
        code=200,
        content_type=content_types.APPLICATION_JSON,
    )


@access_router.get(
    "/users/<shortname>",
    description="Returns a list of all users that have access to the given lab.",
    response_description="A dict containing a list of users with access to the lab.",
    responses={
        **swagger.format_response(
            example={
                "users": [
                    {"username": "user1", "labs": {}, "access": []},
                ],
                "message": "OK",
                "count": 150,
            },
            description="Returns users that can access the lab.",
            code=200,
        ),
        **swagger.format_response(
            example={
                "users": [
                    {"username": "user1", "labs": {}, "access": []},
                ],
                "message": "OK",
                "count": 200,
                "warning": "Return exceded search limit. Try adding '?filter=<value>'",
            },
            description="If number of users exceeds 200, return 200 users and a warning that search is limited to 200 users at a time.",
            code=206,
        ),
        **swagger.code_403,
        **swagger.code_404_lab_not_found,
    },
    tags=[access_route["name"]],
)
@require_access("admin", human=False)
def get_labs_users(shortname):
    user_filter = access_router.current_event.query_string_parameters.get("user_filter")
    email_filter = access_router.current_event.query_string_parameters.get(
        "email_filter"
    )
    row_limit = 200

    # Get users of lab, check if lab exists
    users = get_users_with_lab(
        shortname,
        limit=row_limit,
        username_filter=user_filter,
        email_filter=email_filter,
    )

    out_payload = {
        "users": users,
        "message": "OK",
        "count": len(users),
    }

    if len(users) >= row_limit:
        out_payload["warning"] = (
            "Return exceded search limit. Try adding '?filter=<value>'"
        )

    return wrap_response(
        body=json.dumps(out_payload, default=str),
        code=200 if "warning" not in out_payload else 206,
        content_type=content_types.APPLICATION_JSON,
    )


@access_router.put(
    "/labs/<username>",
    description="""
Sets what labs a user can access. Can be used to both add/remove labs.

<hr>

`PUT` payload should be a json dict of labs and desired user access.

```json
{
    "labs": {
        "<lab_name>": {
            "lab_profiles": ["m6a.large"],
            "time_quota": "",
            "lab_country_status": "protected",
        }
    }
}
```

`{username}` will only have access to `<lab_name>` with profile `m6a.large`.
Any previously added labs not listed in dictionary, will be removed from the user.
    """,
    response_description="A dict containing if it's successful.",
    responses={
        **swagger.code_200_result_success,
        **swagger.code_400_json,
        **swagger.code_403,
        **swagger.code_422,
    },
    tags=[access_route["name"]],
)
@require_access("admin", human=False)
def set_user_labs(username):
    # Check user exists
    user = User(username=username, create_if_missing=False)

    # Parse request body
    body = access_router.current_event.body
    body = json_body_to_dict(body)

    # Validated payload
    success, result = validate_set_lab_access(put_lab_request=body)
    if success:
        user.set_labs(formatted_labs=body["labs"])

    return wrap_response(
        body=json.dumps({"result": result, "body": body}),
        code=200 if success else 422,
        content_type=content_types.APPLICATION_JSON,
    )


@access_router.delete(
    "/labs/<username>",
    description="""
Removes labs from a user. Does not affect labs not listed.

<hr>

`DELETE` payload should be a json dict of labs to be removed from a user. <br />

```json
{
    "labs": {
        "<remove_lab>": {},
    }
}
```

`{username}` will lose access to `<remove_lab>`.

    """,
    response_description="A dict containing if it's successful.",
    responses={
        **swagger.code_200_result_success,
        **swagger.code_400_json,
        **swagger.code_403,
        **swagger.code_422,
    },
    tags=[access_route["name"]],
)
@require_access("admin", human=False)
def delete_user_labs(username):
    # Check user exists
    user = User(username=username, create_if_missing=False)

    # Parse request body
    body = access_router.current_event.body
    body = json_body_to_dict(body)

    # Validated payload
    success, result = validate_delete_lab_access(delete_lab_request=body, user=user)
    if success:
        for lab_name in body["labs"].keys():
            if lab_name in user.labs:
                user.remove_lab(lab_name)

    return wrap_response(
        body=json.dumps({"result": result, "body": body}),
        code=200 if success else 422,
        content_type=content_types.APPLICATION_JSON,
    )


@access_router.get("/apply/<shortname>", include_in_schema=False)
@require_access(human=True)
@portal_template()
def apply_to_lab(shortname):
    if not LAB_CONFIGS.get(shortname):
        return wrap_response(
            body="Redirecting to Portal",
            headers={"Location": "/portal"},
            code=302,
        )

    template_input = {
        "labname": shortname,
        "lab_friendly_name": LAB_CONFIGS[shortname].friendly_name,
        "application_questions": LAB_CONFIGS[shortname].application_questions,
    }
    return jinja_template(template_input, "application.j2")


@access_router.post("/apply/<shortname>", include_in_schema=False)
@require_access(human=True)
def submit_application(shortname):
    # Grab the username of the user making the request
    username = current_session.auth.cognito.username
    # Parse request
    body = access_router.current_event.body

    if body is None:
        error = "Body not provided to submit_application"
        logger.error(error)
        raise MalformedRequest(error)
    body = form_body_to_dict(body)

    # Add Application
    lab = Lab(shortname)
    lab.add_access_request(
        answers=body,
        username=username,
    )

    # Send the user to home page
    return wrap_response(
        body="Redirecting to Portal",
        headers={"Location": "/portal"},
        code=302,
    )
