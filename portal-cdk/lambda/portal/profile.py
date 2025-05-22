from util.format import portal_template
from util.auth import require_access, get_user_from_event
from pathlib import Path
import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(service="APP", level="DEBUG")

profile_router = Router()

profile_route = {
    "router": profile_router,
    "prefix": "/portal/profile",
    "name": "Profile",
}


# This catches "/portal/profile", but "/portal/profile" is uncatchable
@profile_router.get("")
@require_access()
@portal_template(profile_router)
def profile_root():
    page_components = {"input": {}, "content": "Profile Base 1"}
    return page_components


@profile_router.get("/bob")
@require_access()
@portal_template(profile_router)
def profile_bob():
    page_components = {"input": {}, "content": "Profile Bob"}
    username = get_user_from_event(profile_router)
    if username != "bob":
        page_components["contents"] = "You are <b>NOT</b> Bob!"
        return "You are <b>NOT</b> Bob!"

    return page_components


@profile_router.get("/<user>")
@require_access()
@portal_template(profile_router, name="profile.j2")
def profile_user(user):
    page_dict = {
        "content": f"Profile for user {user}",
        "input": {
            "default_value": "Choose...",
        },
    }

    CWD = Path(__file__).parent.resolve().absolute()
    with open(CWD / "../data/countries.json", "r") as f:
        page_dict["input"]["countries"] = json.loads(f.read())
    return page_dict
