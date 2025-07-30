from util.format import portal_template, jinja_template
from util.auth import require_access
from util.user.dynamo_db import list_users_with_lab
from util.user import User
from util.responses import wrap_response, form_body_to_dict
from labs import labs_dict

from aws_lambda_powertools.event_handler.api_gateway import Router

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

    lab = labs_dict[shortname]
    template_input["lab"] = lab

    users = list_users_with_lab(lab.short_lab_name)
    template_input["users"] = users

    return jinja_template(template_input, "manage.j2")


@access_router.post("/manage/<shortname>/edituser")
@require_access("admin")
def edit_user(shortname):
    # Parse request
    body = access_router.current_event.body
    
    if body is None:
        error="Body not provided to edit_user"
        print(error)
        return ValueError(error)
    body = form_body_to_dict(body)

    # Validate request
    # do not add checkboxs here, handle them in Edit user section
    keys = ["action", "username", "lab_profiles", "time_quota", "lab_country_status"]
    for key in keys:
        if key not in body:
            error=f"{key} not provided to edit_user"
            print(error)
            return ValueError(error)

    # Edit user
    if body["action"] == "add":
        # Map checkboxes to True and False
        try:
            body["can_user_see_lab_card"]
            can_user_see_lab_card = True
        except KeyError:
            can_user_see_lab_card = False
            
        try:
            body["can_user_access_lab"]
            can_user_access_lab = True
        except KeyError:
            can_user_access_lab = False
        
        user = User(body["username"])
        user.add_lab(lab_short_name=shortname, lab_profiles=body["lab_profiles"], time_quota=body["time_quota"],
                     lab_country_status=body["lab_country_status"], can_user_access_lab=can_user_access_lab,
                     can_user_see_lab_card=can_user_see_lab_card)
    elif body["action"] == "remove":
        user = User(body["username"])
        user.remove_lab(shortname)
    else:
        error=f"Invalid edit_user action {body['action']}"
        print(error)
        return ValueError(error)

    # Send the user to the management page
    next_url = f"/portal/access/manage/{shortname}"
    return wrap_response(
        body={f"Redirect to {next_url}"},
        code=302,
        headers={"Location": next_url},
    )


@access_router.get("/lab/<lab>")
@require_access()
@portal_template()
def view_lab(lab):
    return f"inspect lab {lab}"
