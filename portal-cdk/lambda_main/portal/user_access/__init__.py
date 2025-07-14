import mimetypes
import os
import pathlib

#from util.format import portal_template
from util.auth import require_access

from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools import Logger

logger = Logger(child=True)

user_access_router = Router()
user_access_route = {
    "router": user_access_router,
    "prefix": "/portal/user-access",
    "name": "User Access"
}

routes = {}
route_names = {}

# Import Nested routes, eg /portal/user-access/...
for route in (user_access_route,):
    routes[route["prefix"]] = route["router"]

    if "name" in route:
        route_names[route["name"]] = route["prefix"]

def get_response(event_path: str):
    # Don't include the url path /user-access as part fo the file path
    # ./dist/ is the within the file path root.
    file_path = event_path.removeprefix("/portal").removeprefix("/user-access").removeprefix("/dist")
    file_path = "/dist/" + file_path.removeprefix("/").removeprefix("./")

    local_path = pathlib.Path.cwd() / pathlib.Path(__file__).parent
    abs_file_path = str(local_path) + file_path

    logger.debug(f"{local_path=} {file_path=} {abs_file_path=}")

    if not os.path.exists(abs_file_path):
        raise NotFoundError(f"{file_path} (aka {abs_file_path}) not found")

    with open(abs_file_path, "rb") as file_obj:
        body = file_obj.read()

    mime_type, encoding = mimetypes.guess_type(abs_file_path)
    if not mime_type:
        logger.warning(
            f"Mimetype for file {abs_file_path=} not recognized. This might crash the site."
        )

    return Response(
        status_code=200,
        content_type=mime_type,
        body=body,
    )

# Pass router into require_access for accessing `app`
# portal_router.app doesn't exist _yet_, but will later. And we'll need access.
require_access.router = user_access_router

@user_access_router.get("")
@require_access()
# @portal_template() ## Overwrites HTML response incorrectly
def user_access_root():
    event_path = "index.html"
    logger.debug("Path is %s", event_path)
    return get_response(event_path)


@user_access_router.get(".+")
@require_access()
# @portal_template() ## Overwrites HTML response incorrectly
def user_access():
    event_path = str(user_access_router.current_event.path)
    logger.debug("Path is %s", event_path)
    return get_response(event_path)
