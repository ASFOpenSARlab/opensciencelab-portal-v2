from portal.profile import profile_route
from portal.access import access_route
from portal.hub import hub_route
from portal.users import users_route
from util.format import portal_template
from util.auth import require_access
from util.session import current_session
from util.user import User
from labs import labs_dict

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
for route in (portal_route, profile_route, access_route, hub_route, users_route):
    routes[route["prefix"]] = route["router"]

    if "name" in route:
        route_names[route["name"]] = route["prefix"]

# Pass router into require_access for accessing `app`
# portal_router.app doesn't exist _yet_, but will later. And we'll need access.
require_access.router = portal_router


@portal_router.get("")
@require_access()
@portal_template(name="portal.j2")
def portal_root():
    page_dict = {
        "content": "List All Labs",
        "input": {},
    }
    username = current_session.auth.cognito.username
    user = User(username=username)

    # Get all labs as a list
    labs = list(labs_dict.values())

    # Filter by labs the user has access to
    for index, lab in enumerate(labs):
        # Remove all labs the user is not given access to
        if lab.short_lab_name not in user.labs:
            labs.pop(index)

    # Add labs to page_dict
    page_dict["input"]["labs"] = labs

    # Add admin check to formatting
    page_dict["input"]["admin"] = user.is_admin()
    return page_dict
