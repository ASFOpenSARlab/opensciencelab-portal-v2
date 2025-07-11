import mimetypes
import os
import pathlib

from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools import Logger

logger = Logger(service="APP", level="DEBUG")


def get_dist_object(event):

    # Don't include the /user-access as part fo the file path
    full_url_path = pathlib.Path(event.path)
    # Get rid of the prepended '.'
    file_ext = full_url_path.suffix[1:]
    file_path = str(full_url_path).removeprefix("/user-access")

    local_path = pathlib.Path.cwd() / pathlib.Path(__file__).parent
    abs_file_path = str(local_path) + file_path

    logger.debug(f"get_dist_object {event.path=} {file_path=} {file_ext=}")
    logger.debug(f"get_dist_object {abs_file_path=} {local_path=} {file_path=}")

    if not os.path.exists(abs_file_path):
        raise NotFoundError(f"{file_path} (aka {abs_file_path}) not found")

    with open(abs_file_path, "rb") as file_obj:
        body = file_obj.read()

    logger.debug(f"{body=}")

    mime_type, encoding = mimetypes.guess_type(file_ext)

    logger.debug(f"{mime_type=} {encoding=}")

    # guess_type gets these wrong
    if file_ext == "css":
        mime_type = "text/css"
    elif file_ext == "js":
        mime_type = "text/javascript"
    elif file_ext == "png":
        mime_type = "image/png"
    elif file_ext == "html":
        mime_type = "text/html"
    elif file_ext == 'svg':
        mime_type = "image/svg+xml"

    return Response(
        status_code=200,
        content_type=mime_type,
        body=body,
    )
