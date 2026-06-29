import json
import csv
import io
from dataclasses import asdict
from datetime import datetime

from util import swagger
from util.format import portal_template, jinja_template
from util.auth import require_access
from util.session import current_session
from objs.user import (
    User,
    get_users_with_lab,
    filter_lab_access,
    get_users_with_lab_lazy,
)
from util.responses import wrap_response, form_body_to_dict, json_body_to_dict
from util.labs import LAB_CONFIGS
from objs.lab import Lab, ACTIVE_REQUEST_STATUSES
from util.exceptions import MalformedRequest
from util.dynamo_db import dynamo_filter, get_all_items, combine_all_dynamo_filters
from util.manage_access import (
    validate_edit_user_request,
    validate_delete_lab_access,
    validate_set_lab_access,
    validate_edit_tokens_request,
    validate_edit_manager_permission_request,
)
from util.access_request import request_status_change_action, process_access_token
from util.send_email import send_user_email

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

# Display sort order for access requests. Higher numbers, top of page
SORT_ORDER = {
    "new": 6,
    "pending": 5,
    "returned": 4,
    "approved": 3,
    "rejected": 2,
    "imported": 1,
}


# This catches "/portal/access" (this routers 'root'):
@access_router.get("", include_in_schema=False)
@require_access(["admin"], human=True)
@portal_template()
def access_root() -> str:
    user_filter = access_router.current_event.query_string_parameters.get("user_filter")
    state_filter = access_router.current_event.query_string_parameters.get(
        "status_filter"
    )

    # Are results filtered?
    filtered = True if user_filter or state_filter else False

    # Apply Filters
    filter = dynamo_filter(
        attr_name="status",
        filter_value=[state_filter] if state_filter else ["new", "pending"],
        filter_action="in",
    )

    if user_filter:
        filter = combine_all_dynamo_filters(
            [filter, dynamo_filter("username", user_filter)]
        )

    requests = get_all_items(table_id="request", limit=200, filters=filter)
    requests = sorted(
        requests,
        key=lambda x: (SORT_ORDER.get(x["status"], 0), x.get("last_update", "x")),
        reverse=True,
    )

    template_input = {
        "requests": requests,
        "filter_path": "/portal/access",
        "filtered": filtered,
    }

    logger.info(f"template_input = {template_input}")

    return jinja_template(template_input, "manage_access.j2")


@access_router.get("/manage/<shortname>/requests/", include_in_schema=False)
@require_access(["admin", "lab_manager"], human=True)
@portal_template()
def list_access_requests(shortname):
    user_filter = access_router.current_event.query_string_parameters.get("user_filter")
    state_filter = access_router.current_event.query_string_parameters.get(
        "status_filter"
    )

    lab = Lab(labname=shortname)

    requests = lab.get_requests()

    # Apply filters
    if user_filter:
        requests = [r for r in requests if user_filter in r["username"]]
    if state_filter:
        requests = [r for r in requests if r["status"] == state_filter]

    # Sort by status, last updated
    requests = sorted(
        requests,
        key=lambda x: (SORT_ORDER.get(x["status"], 0), x.get("last_update", "x")),
        reverse=True,
    )

    # Make sure we don't return > 200 records
    if len(requests) > 200:
        requests = requests[:200]

    template_input = {"requests": requests}
    return jinja_template(template_input, "manage_access.j2")


@access_router.get(
    "/manage/<shortname>/raw_request/<username>/", include_in_schema=False
)
@require_access(["admin"], human=True)
def get_raw_access_request(shortname, username):
    lab = Lab(labname=shortname)
    request_data = lab.get_access_request(username)
    return wrap_response(
        body=json.dumps(request_data, default=str),
        code=200 if request_data else 422,
        content_type=content_types.APPLICATION_JSON,
    )


@access_router.post("/manage/<shortname>/update/<username>/", include_in_schema=False)
@require_access(["admin"], human=True)
def update_user_access_request(shortname, username):
    status_map = {
        "Reject": "rejected",
        "Approve": "approved",
        "Pending": "pending",
        "Return": "returned",
    }

    lab = Lab(labname=shortname)
    # Grab the username of the user making the request
    admin_username = current_session.auth.cognito.username

    # Parse request
    body = access_router.current_event.body
    if body is None:
        raise MalformedRequest("Malformed update request payload")
    body = form_body_to_dict(body)

    comment = body.get("comment", None)
    status = status_map.get(body.get("status"))

    # Take specific actions
    request_status_change_action(lab, username, status)

    # Change status
    lab.set_access_request_status(
        username=username,
        status=status,
        reviewer=admin_username,
        reviewer_comment=comment,
    )

    # Send the reviewer back to the user's profile
    next_url = f"/portal/profile/form/{username}"
    return wrap_response(
        body={f"Redirect to {next_url}"},
        code=302,
        headers={"Location": next_url},
    )


@access_router.get("/manage/<shortname>/export-users", include_in_schema=False)
@require_access(["admin", "lab_manager"], human=True)
def export_users(shortname):
    # Get lab info
    lab = LAB_CONFIGS[shortname]

    users = get_users_with_lab(shortname)
    buf = io.StringIO()
    writer = csv.writer(buf)

    # Write columns
    columns = ["username", "profiles", "email"]
    if lab.allows_tokens:
        columns.append("token")
    writer.writerow(columns)

    for user in users:
        values = [user["username"], user["labs"][shortname]["lab_profiles"], user["email"]]
        if lab.allows_tokens:
            values.append([token["token"] for token in user["token_usage"]])
        writer.writerow(values)

    return wrap_response(
        body=buf.getvalue(),
        code=200,
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'attachment; filename="users.csv"',
            "Cache-Control": "no-store",
        },
    )


@access_router.get("/manage/<shortname>/get-users", include_in_schema=False)
@require_access(["admin", "lab_manager"], human=True)
def get_users(shortname):
    user_filter = access_router.current_event.query_string_parameters.get("user_filter")
    email_filter = access_router.current_event.query_string_parameters.get(
        "email_filter"
    )
    row_limit = 100
    primary_key = access_router.current_event.query_string_parameters.get("primary_key")
    key_value = access_router.current_event.query_string_parameters.get("key_value")

    exclusive_start_key = (
        {primary_key: key_value} if primary_key and key_value else None
    )

    users, lastEvaluatedKey = get_users_with_lab_lazy(
        shortname,
        limit=row_limit,
        username_filter=user_filter,
        email_filter=email_filter,
        exclusive_start_key=exclusive_start_key,
        minimum_results=row_limit * 0.75,
    )

    # Whitelist specific keys
    keys = ["labs", "username", "email", "token_usage"]
    users = [{k: user[k] for k in keys} for user in users]

    return {"users": users, "lastEvaluatedKey": lastEvaluatedKey}


@access_router.get("/manage/<shortname>", include_in_schema=False)
@require_access(["admin", "lab_manager"], human=True)
@portal_template()
def manage_lab(shortname):
    template_input = {}

    user_filter = access_router.current_event.query_string_parameters.get("user_filter")
    email_filter = access_router.current_event.query_string_parameters.get(
        "email_filter"
    )
    row_limit = 200

    # Are results filtered?
    filtered = True if user_filter or email_filter else False

    # Grab the username of the user making the request
    username = current_session.auth.cognito.username
    user = User(username)
    lab = LAB_CONFIGS[shortname]
    lab_obj = Lab(shortname)

    template_input["is_admin"] = user.is_admin()

    # Get users of lab, check if lab exists
    users = get_users_with_lab(
        shortname,
        limit=row_limit,
        username_filter=user_filter,
        email_filter=email_filter,
    )
    # Add is_manager field to visible users who are managers
    managers = set(lab_obj.managers)
    for user in users:
        if user["username"] in managers:
            user["is_manager"] = True
            managers.remove(user["username"])
    users = sorted(users, key=lambda x: x["username"])
    template_input["users"] = users

    template_input["lab"] = lab
    template_input["managers"] = list(set(lab_obj.managers))
    template_input["allows_requests"] = len(lab.application_questions) > 0
    template_input["rowcount"] = len(users)
    template_input["exceeded"] = len(users) >= row_limit
    template_input["access_tokens"] = lab_obj.access_tokens
    template_input["filter_path"] = f"/portal/access/manage/{shortname}"
    template_input["filtered"] = filtered

    return jinja_template(template_input, "manage.j2")


@access_router.post("/manage/<shortname>/edituser", include_in_schema=False)
@require_access(["admin", "lab_manager"], human=True)
def edit_user(shortname):
    # Grab the username of the user making the request
    caller_username = current_session.auth.cognito.username

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
        lab_access: bool = user.get_lab_access()["lab_access"].get(shortname, {})
        update: bool = lab_access.get("can_user_access_lab", False)

        user.add_lab(
            lab_short_name=shortname,
            lab_profiles=[s.strip() for s in body["lab_profiles"].split(",")],
        )
        if update:
            logger.info(
                f'{caller_username} updated access for user "{body["username"]}" in {shortname}'
            )
        else:
            logger.info(
                f'{caller_username} added user "{body["username"]}" to {shortname}'
            )

    elif body["action"] == "remove_user":
        user.remove_lab(shortname)
        logger.info(
            f'{caller_username} removed user "{body["username"]}" from {shortname}'
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


@access_router.post("/manage/<shortname>/editmanager", include_in_schema=False)
@require_access(["admin", "lab_manager"], human=True)
def edit_manager_permission(shortname):
    # Grab the username of the user making the request
    caller_username = current_session.auth.cognito.username

    # Parse request
    body = access_router.current_event.body

    if body is None:
        error = "Body not provided to edit_user"
        logger.error(error)
        raise MalformedRequest(error)
    body = form_body_to_dict(body)

    # Validate request
    success, message = validate_edit_manager_permission_request(body=body)
    if not success:
        logger.error(message)
        raise MalformedRequest(message)

    # Edit manager permissions
    user = User(body["username"])
    lab = Lab(shortname)

    if body["action"] == "grant":
        if "lab_manager" not in user.access:
            user.grant_access_role("lab_manager")
        lab.add_manager(body["username"])
        logger.info(
            f'{caller_username} granted lab_manager to "{body["username"]}" in {shortname}'
        )

    elif body["action"] == "revoke":
        lab.remove_manager(body["username"])
        still_manager = False
        for labname in LAB_CONFIGS.keys():
            if body["username"] in Lab(labname).managers:
                still_manager = True
                break
        if not still_manager:
            user.revoke_access_role("lab_manager")
        logger.info(
            f'{caller_username} revoked lab_manager from "{body["username"]}" in {shortname}'
        )

    else:
        error = f"Invalid edit_manager_permission action {body['action']}"
        logger.error(error)
        raise MalformedRequest(error)

    # Send the user to the management page
    next_url = f"/portal/access/manage/{shortname}"
    return wrap_response(
        body={f"Redirect to {next_url}"},
        code=302,
        headers={"Location": next_url},
    )


@access_router.post("/manage/<shortname>/edittokens", include_in_schema=False)
@require_access(["admin", "lab_manager"], human=True)
def edit_tokens(shortname):
    # Grab the username of the user making the request
    caller_username = current_session.auth.cognito.username

    lab = Lab(shortname)

    # Parse request
    body = access_router.current_event.body

    if body is None:
        error = "Body not provided to edit_tokens"
        logger.error(error)
        raise MalformedRequest(error)
    body = form_body_to_dict(body)

    # Validate request
    success, message = validate_edit_tokens_request(body=body)
    if not success:
        logger.error(message)
        raise MalformedRequest(message)

    # Edit tokens
    if body["action"] == "add_token":
        start_date = (
            datetime.strptime(body["start_date"], "%Y-%m-%d")
            if body["start_date"]
            else None
        )
        end_date = (
            datetime.strptime(body["end_date"], "%Y-%m-%d")
            if body["end_date"]
            else None
        )

        if start_date and end_date:
            if start_date >= end_date:
                # Send the user to the management page
                next_url = f"/portal/access/manage/{shortname}/edittokens"
                return wrap_response(
                    body={f"Redirect to {next_url}"},
                    code=302,
                    headers={"Location": next_url},
                )

        success = lab.create_access_token(
            start_date=start_date,
            end_date=end_date,
            profiles=[s.strip() for s in body["lab_profiles"].split(",")],
        )
        if success:
            logger.info(f"{caller_username} added token to {shortname}")

    elif body["action"] == "remove_token":
        success = lab.remove_access_token(body["token"])
        if success:
            logger.info(f"{caller_username} removed token from {shortname}")

    else:
        error = f"Invalid edit_tokens action {body['action']}"
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
@require_access(["admin"], human=False)
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
@require_access(["admin"], human=False)
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
@require_access(["admin"], human=False)
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
@require_access(["admin"], human=False)
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

    # Grab the username of the user making the request
    username = current_session.auth.cognito.username

    # user_profile = User(username=username, create_if_missing=False)
    # active_access_requests = user_profile.get_requests(status=["new", "pending"])
    lab = Lab(shortname)
    access_requests = lab.get_access_request(username)

    template_input = {
        "labname": shortname,
        "lab_friendly_name": LAB_CONFIGS[shortname].friendly_name,
        "application_questions": LAB_CONFIGS[shortname].application_questions,
        "lab_application_description": LAB_CONFIGS[shortname].application_description,
    }
    if access_requests and access_requests["status"] in ACTIVE_REQUEST_STATUSES:
        template_input["active_request"] = access_requests["answers"][-1]
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
    # If fixing checkbox implementation, map checkbox values to bool here

    # Add Application
    lab = Lab(shortname)
    lab.add_access_request(
        answers=body,
        username=username,
    )

    application_received_email = {
        "to": {"username": username},
        "from": {username: "osl-admin"},
        "subject": "OpenScienceLab Access Application Received",
        "html_body": (
            f"Hello {username},<br><br>"
            f"We've received your request for access to <b>{LAB_CONFIGS[shortname].friendly_name}</b>.<br>"
            "Applications are evaluated on a weekly basis. We will inform you of any "
            "decision as soon as possible.<br><br>"
            "If you have any concerns about the timeliness of your application review, "
            "please email us at uaf-jupyterhub-admin@alaska.edu.<br><br>"
            "The OpenScienceLab Admin Team"
        ),
    }

    result, reason = send_user_email(application_received_email)
    if result == "Error":
        logger.error(
            f"Application reciept acknowledgement email failed to send: {reason}"
        )

    # Send the user to home page
    return wrap_response(
        body="Redirecting to Portal",
        headers={"Location": "/portal"},
        code=302,
    )


@access_router.get("/token", include_in_schema=False)
@require_access(human=True)
@portal_template()
def input_access_token():
    return jinja_template({}, "token.j2")


@access_router.post("/token", include_in_schema=False)
@require_access(human=True)
@portal_template()
def apply_access_token():
    # Grab the username of the user making the request
    username = current_session.auth.cognito.username
    # Parse request
    body = access_router.current_event.body
    body = form_body_to_dict(body)

    # Grab the token value
    token_value = body["token"]

    # Process the token
    granted = process_access_token(token_value, username)

    if not granted:
        template_input = {"warning": "Token could not be applied"}
        return jinja_template(template_input, "token.j2")

    # Send the user back to portal root
    template_input = {"note": "Token applied!"}
    return jinja_template(template_input, "token.j2")
