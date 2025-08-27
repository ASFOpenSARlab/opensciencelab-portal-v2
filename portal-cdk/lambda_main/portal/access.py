import json

from util.format import portal_template, jinja_template
from util.auth import require_access
from util.user.dynamo_db import get_users_with_lab
from util.user import User
from util.responses import wrap_response, form_body_to_dict
from util.labs import all_labs

from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler import content_types

access_router = Router()

access_route = {
    "router": access_router,
    "prefix": "/portal/access",
    "name": "Access",
}

# This catches "/portal/access"
@access_router.get("")
@require_access()
@portal_template()
def access_root():
    return "Access Labs"


@access_router.get("/add_lab")
@require_access()
@portal_template()
def add_lab():
    return "Create New Lab"


@access_router.get("/manage/<shortname>")
@require_access("admin")
@portal_template()
def manage_lab(shortname):
    template_input = {}

    # Get users of lab, check if lab exists
    users = get_users_with_lab(shortname)
    template_input["users"] = users

    lab = all_labs[shortname]
    template_input["lab"] = lab

    return jinja_template(template_input, "manage.j2")


def validate_edit_user_request(body: dict) -> tuple[bool, str]:
    # check always required keys are provided
    keys = ["username", "action"]
    for key in keys:
        if key not in body:
            return False, f"{key} not provided to edit_user"

    if body["action"] == "add_user":
        # check adding user fields provided
        keys = ["lab_profiles", "time_quota", "lab_country_status"]
        for key in keys:
            if key not in body:
                return False, f"{key} not provided to edit_user"
        return True, "Read to add user"

    elif body["action"] == "remove_user":
        # check removing user fields provided
        return True, "Ready to remove user"

    elif body["action"] == "toggle_can_user_see_lab_card":
        return True, "Ready to toggle can_user_see_lab_card"

    elif body["action"] == "toggle_can_user_access_lab":
        return True, "Ready to toggle can_user_access_lab"

    else:
        return False, "Invalid action"


@access_router.post("/manage/<shortname>/edituser")
@require_access("admin")
def edit_user(shortname):
    # Parse request
    body = access_router.current_event.body

    if body is None:
        error = "Body not provided to edit_user"
        print(error)
        raise ValueError(error)
    body = form_body_to_dict(body)

    # Validate request
    success, message = validate_edit_user_request(body=body)
    if not success:
        print(message)
        raise ValueError(message)

    # Edit user
    user = User(body["username"])

    # Map checkboxes to True and False
    can_user_see_lab_card = "can_user_see_lab_card" in body
    can_user_access_lab = "can_user_access_lab" in body

    if body["action"] == "add_user":
        user.add_lab(
            lab_short_name=shortname,
            lab_profiles=[s.strip() for s in body["lab_profiles"].split(",")],
            time_quota=body["time_quota"].strip() or None,
            lab_country_status=body["lab_country_status"],
            can_user_access_lab=can_user_access_lab,
            can_user_see_lab_card=can_user_see_lab_card,
        )

    elif body["action"] == "remove_user":
        user.remove_lab(shortname)

    elif body["action"] == "toggle_can_user_see_lab_card":
        labs = dict(user.labs)
        labs[shortname] = dict(labs[shortname])
        labs[shortname]["can_user_see_lab_card"] = not user.labs[shortname][
            "can_user_see_lab_card"
        ]
        user.labs = labs

    elif body["action"] == "toggle_can_user_access_lab":
        labs = dict(user.labs)
        labs[shortname] = dict(labs[shortname])
        labs[shortname]["can_user_access_lab"] = not user.labs[shortname][
            "can_user_access_lab"
        ]
        user.labs = labs

    else:
        error = f"Invalid edit_user action {body['action']}"
        print(error)
        raise ValueError(error)

    # Send the user to the management page
    next_url = f"/portal/access/manage/{shortname}"
    return wrap_response(
        body={f"Redirect to {next_url}"},
        code=302,
        headers={"Location": next_url},
    )

@access_router.get("/lab")
@require_access()
@portal_template()
def view_all_labs():
    return "inspect ALL labs"

@access_router.get("/lab/<lab>")
@require_access()
@portal_template()
def view_lab(lab):
    return f"inspect lab {lab}"


@access_router.get("/labs/<username>")
@require_access("admin")
def get_user_labs(username):
    # Find user in db

    user = User(username=username, create_if_missing=False)

    # Return user labs
    return wrap_response(
        body=json.dumps({"labs": user.labs, "message": "OK"}),
        code=200,
        content_type=content_types.APPLICATION_JSON,
    )


@access_router.get("/users/<shortname>")
@require_access("admin")
def get_labs_users(shortname):
    users = get_users_with_lab(shortname)

    return wrap_response(
        body=json.dumps({"users": users, "message": "OK"}),
        code=200,
        content_type=content_types.APPLICATION_JSON,
    )


def validate_set_lab_access(
    put_lab_access: dict, all_labs_in: dict
) -> tuple[bool, str]:
    # Validate input is correct type
    if not isinstance(put_lab_access, dict):
        return False, "Body is not correct type"

    # Validate input has key "labs"
    if put_lab_access.get("labs") is None:
        return False, "Does not contain 'labs' key"

    for lab_name in put_lab_access["labs"].keys():
        # Ensure lab exist
        if lab_name not in all_labs_in:
            return False, f"Lab does not exist: {lab_name}"

        # Check all lab fields exist and are correct type
        all_fields = {
            "lab_profiles": list,
            "can_user_access_lab": bool,
            "can_user_see_lab_card": bool,
            "time_quota": str,
            "lab_country_status": str,
        }
        for field, _ in all_fields.items():
            if put_lab_access["labs"][lab_name].get(field) is None:
                return False, f"Field '{field}' not provided for lab {lab_name}"

            if not isinstance(
                put_lab_access["labs"][lab_name][field], all_fields[field]
            ):
                return False, f"Field '{field}' not of type {all_fields[field]}"

        # NOT IMPLEMENTED YET
        # # Ensure all profiles exist for a given lab
        # for profile in put_lab_access["labs"][lab_name]["lab_profiles"]:
        #     pass
    return True, "Success"


@access_router.put("/labs/<username>")
@require_access("admin")
def set_user_labs(username):
    # Check user exists
    user = User(username=username, create_if_missing=False)

    # Parse request body
    body = access_router.current_event.body

    try:
        body = json.loads(body)
    except json.JSONDecodeError as e:
        return wrap_response(
            body=json.dumps({
                "result": "Malformed JSON",
                "error": str(e),
                "body": body
            }),
            code=400,
            content_type=content_types.APPLICATION_JSON,
        )

    # Validated payload
    success, result = validate_set_lab_access(put_lab_access=body, all_labs_in=all_labs)
    if success:
        user.set_labs(formatted_labs=body["labs"])
    return wrap_response(
        body=json.dumps({"result": result, "body": body}),
        code=200 if success else 422,
        content_type=content_types.APPLICATION_JSON,
    )
