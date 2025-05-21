from portal.profile import profile_route
from portal.access import access_route
from portal.hub import hub_route
from util.format import portal_template
from util.auth import require_access


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
for route in (portal_route, profile_route, access_route, hub_route):
    routes[route["prefix"]] = route["router"]

    if "name" in route:
        route_names[route["name"]] = route["prefix"]

# Pass router into require_access for accessing `app`
# portal_router.app doesn't exist _yet_, but will later. And we'll need access.
require_access.router = portal_router


@portal_router.get("")
@require_access()
@portal_template(portal_router)
def portal_root():
    return "Welcome to OpenScienceLab"
