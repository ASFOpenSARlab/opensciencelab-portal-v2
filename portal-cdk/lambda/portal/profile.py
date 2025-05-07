from portal.format import portal_template
from portal.responses import basic_html

from aws_lambda_powertools.event_handler.api_gateway import Router

profile_router = Router()

profile_route = {
    "router": profile_router,
    "prefix": "/portal/profile",
    "name": "Profile",
}


# This catches "/portal/profile", but "/portal/profile" is uncatchable
@profile_router.get("")
@basic_html()
@portal_template(profile_router)
def profile_root():
    return "Profile Base 1"


@profile_router.get("/bob")
@basic_html()
@portal_template(profile_router)
def profile_bob():
    return "Profile Bob"


@profile_router.get("/<user>")
@basic_html()
@portal_template(profile_router)
def profile_user(user):
    return f"Profile for user {user}"
