from portal.profile import profile_route
from portal.access import access_route
from portal.hub import hub_route
from portal.users import users_route
from portal.mfa import mfa_route
from portal.notifications import notifications_route
from util.format import portal_template, jinja_template
from util.auth import require_access
from util.session import current_session
from objs.user import User
from objs.lab import Lab

from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools import Logger

logger = Logger(child=True)

portal_router = Router()
portal_route = {
    "router": portal_router,
    "prefix": "/portal",
    "name": "Home",
}

routes = {}
route_names = {}

# Import Nested routes, eg /portal/profile
for route in (
    portal_route,
    profile_route,
    access_route,
    hub_route,
    users_route,
    mfa_route,
    notifications_route,
):
    routes[route["prefix"]] = route["router"]

    if "name" in route:
        route_names[route["name"]] = route["prefix"]

# Pass router into require_access for accessing `app`
# portal_router.app doesn't exist _yet_, but will later. And we'll need access.
require_access.router = portal_router


@portal_router.get("", include_in_schema=False)
@require_access(human=True)
@portal_template()
def portal_root():

    username = current_session.auth.cognito.username
    user = User(username=username)

    # Filter by labs the user has access to
    lab_access = user.get_lab_access()
    # Get Lab obj for labs the user can see
    lab_objs = {key: Lab(key) for key in lab_access["viewable_labs_config"]}
    lab_access["viewable_labs_config"] = lab_objs

    template_input = {
        "username": username,
        "labs": lab_access,
        "admin": user.is_admin(),
    }
    return jinja_template(template_input, "portal.j2")
