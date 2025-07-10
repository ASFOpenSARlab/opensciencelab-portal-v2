import json
from base64 import b64decode
from urllib.parse import parse_qs
from typing import Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import (
    Response,
    content_types,
)

logger = Logger(child=True)


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
        if isinstance(cookies, dict):
            # if a dict was passed in, format at list
            cookies = [f"{k}={v};" for k, v in cookies.items()]

        response_payload["cookies"] = cookies

    logger.info(response_payload)

    return Response(**response_payload)

def form_body_to_dict(body:str) -> dict:
    """Converts an html form body to a python dictionary

    Args:
        body (str): Body of an html form

    Returns:
        dict: Python dictionary with key values provided from body
    """
    body = b64decode(body)
    parsed_qs = parse_qs(body, keep_blank_values=True)
    query_dict: dict[str, Any] = {
        k.decode("utf-8"): v[0].decode("utf-8") for k, v in parsed_qs.items()
    }
    return query_dict