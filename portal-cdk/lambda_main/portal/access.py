from util.format import portal_template
from util.auth import require_access
from util.user.dynamo_db import list_users_with_lab
from util.user import User
from labs import labs_dict

import json

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
@require_access()
@portal_template(name="manage.j2")
def manage_lab(shortname):
    page_dict = {
        "content": "Manage Lab",
        "input": {
        },
    }
    
    lab = labs_dict[shortname]
    page_dict["input"]["lab"] = lab
    
    users = list_users_with_lab(lab.short_lab_name)
    page_dict["input"]["users"] = users
    
    return page_dict


@access_router.post("/manage/<shortname>/edituser")
@require_access()
def edit_user(shortname):
    # Parse request
    body = access_router.current_event.body
    if body is None:
        return ValueError("Body not provided to edit_user")
    body:dict = json.loads(body)
    
    # Validate request
    if "action" not in body:
        return ValueError("Action not provided to edit_user")
    if "username" not in body:
        return ValueError("Username not provided to edit_user")
    
    # Edit user
    if body["action"] == "add":
        user = User(body["username"])
        user.add_lab(shortname)
    elif body["action"] == "remove":
        user = User(body["username"])
        user.remove_lab(shortname)
    else:
        return ValueError(f"Invalid edit_user action {body['action']}")


@access_router.get("/lab/<lab>")
@require_access()
@portal_template()
def view_lab(lab):
    return f"inspect lab {lab}"
