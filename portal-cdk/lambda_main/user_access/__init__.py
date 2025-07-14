import mimetypes
import os
import pathlib

from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools import Logger

logger = Logger(service="APP", level="DEBUG")


def get_dist_object(event_path: str):
    # Don't include the url path /user-access as part fo the file path
    # ./dist/ is the within the file path root.
    file_path = event_path.removeprefix("/user-access").removeprefix("/dist")
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
