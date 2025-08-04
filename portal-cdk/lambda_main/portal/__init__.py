from portal.profile import profile_route
from portal.access import access_route
from portal.hub import hub_route
from portal.users import users_route
from util.format import portal_template, jinja_template
from util.auth import require_access
from util.session import current_session
from util.user import User

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
@portal_template()
def portal_root():
    template_input = {}

    username = current_session.auth.cognito.username
    user = User(username=username)

    # Filter by labs the user has access to
    lab_access_info = user.get_lab_access()

    # Add labs to page_dict
    template_input["labs"] = lab_access_info

    ## Curently missing ##
    ## Lab ordering
    ## is_global_lab_country_status_limited warning
    ## is_mfa_enabled warning

    # Add admin check to formatting
    template_input["admin"] = user.is_admin()

    return jinja_template(template_input, "portal.j2")
