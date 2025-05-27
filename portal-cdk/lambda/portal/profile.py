from util.format import portal_template
from util.auth import require_access
from util.session import current_session

from aws_lambda_powertools.event_handler.api_gateway import Router

profile_router = Router()

profile_route = {
    "router": profile_router,
    "prefix": "/portal/profile",
    "name": "Profile",
}


# This catches "/portal/profile", but "/portal/profile" is uncatchable
@profile_router.get("")
@require_access()
@portal_template()
def profile_root():
    return "Profile Base 1"


@profile_router.get("/bob")
@require_access()
@portal_template()
def profile_bob():
    username = current_session.auth.cognito.username
    if username != "bob":
        return "You are <b>NOT</b> Bob!"

    return "Profile Bob"


@profile_router.get("/<user>")
@require_access()
@portal_template()
def profile_user(user):
    return f"Profile for user {user}"
