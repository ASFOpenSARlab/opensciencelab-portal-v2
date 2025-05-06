from portal.profile import profile_route
from portal.access import access_route

routes = {}
route_names = []

for route in (profile_route, access_route):
    routes["prefix"] = routes["router"]
    route_names.append(routes["name"])
