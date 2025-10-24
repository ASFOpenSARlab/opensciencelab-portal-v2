import mimetypes
import os

from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.event_handler import Response


def read_file(read_path):
    local_path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    abs_file_path = os.path.join(local_path, read_path)

    if not os.path.exists(abs_file_path):
        raise NotFoundError(f"{read_path} (aka {abs_file_path}) not found")

    file_obj = open(abs_file_path, "rb")
    return file_obj.read()


def get_static_object(event):
    file_type, file_name = event.path.split("/")[2:4]
    file_ext = file_name.split(".")[-1]

    if file_type not in ("css", "js", "img", "fonts"):
        raise NotFoundError(f"{event.path} not found")

    body = read_file(os.path.join(file_type, file_name))

    mime_type, encoding = mimetypes.guess_type(file_ext)

    # guess_type gets these wrong
    if file_ext == "css":
        mime_type = "text/css"
    if file_ext == "js":
        mime_type = "text/javascript"
    if file_ext == "png":
        mime_type = "image/png"
    if file_ext == "svg":
        mime_type = "image/svg+xml"

    return Response(
        status_code=200,
        content_type=mime_type,
        body=body,
    )
