from portal_formatting import portal_template, basic_html

from aws_lambda_powertools.event_handler.api_gateway import Router

profile_router = Router()

profile_route = {
    "router": profile_router,
    "prefix": "/portal/profile",
    "name": "profile",
}


# This catches "/portal/profile", but "/portal/profile" is uncatchable
@profile_router.get("")
def profile_root():
    return basic_html(portal_template("Profile Base 1"))


@profile_router.get("/bob")
def profile_bob():
    return basic_html(portal_template("Profile Bob"))


@profile_router.get("/<user>")
def profile_user(user):
    return basic_html(portal_template(f"Profile for user {user}"))
