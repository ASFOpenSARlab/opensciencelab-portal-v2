from portal.profile import profile_route
from portal.access import access_route
from portal.format import portal_template

from aws_lambda_powertools.event_handler.api_gateway import Router

portal_router = Router()
portal_route = {
    "router": portal_router,
    "prefix": "/portal",
    "name": "Home",
}

routes = {}
route_names = {}

# Import Nested routes, eg /portal/profile
for route in (portal_route, profile_route, access_route):
    routes[route["prefix"]] = route["router"]
    route_names[route["name"]] = route["prefix"]


@portal_router.get("")
@portal_template(portal_router)
def portal_root():
    return "Welcome to OpenScienceLab"
