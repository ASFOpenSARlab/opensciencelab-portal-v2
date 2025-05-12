import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import (
    Response,
    content_types,
)

logger = Logger(service="APP")


def wrap_response(body, code=200, content_type=None, headers=None, cookies=None):
    response_payload = {
        "content_type": content_type,
        "status_code": code,
        "body": body,
    }

    if not isinstance(body, str):
        response_payload["body"] = json.dumps(body, default=str)
    if not content_type:
        response_payload["content_type"] = content_types.TEXT_HTML
    if headers:
        response_payload["headers"] = headers
    if cookies:
        response_payload["cookies"] = cookies

    logger.info(response_payload)

    return Response(**response_payload)


def basic_html(code=None, content_type=None, headers=None, cookies=None):
    # username will eventually come from app
    def inner(func):
        def wrapper(*args, **kwargs):
            body = func(*args, **kwargs)
            return wrap_response(body, code, content_type, headers, cookies)

        return wrapper

    return inner


def basic_json(
    code=None, content_type=content_types.APPLICATION_JSON, headers=None, cookies=None
):
    def inner(func):
        def wrapper(*args, **kwargs):
            body = func(*args, **kwargs)
            return wrap_response(body, code, content_type, headers, cookies)

        return wrapper

    return inner
