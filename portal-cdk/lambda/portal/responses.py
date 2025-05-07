from aws_lambda_powertools.event_handler import (
    Response,
    content_types,
)


def wrap_response(body, code=200, content_type=None, headers=None, cookies=None):
    response_payload = {
        "status_code": code,
        "body": body,
    }

    if not content_type:
        response_payload["content_type"] = content_types.TEXT_HTML
    if headers:
        response_payload["headers"] = headers
    if cookies:
        response_payload["cookies"] = cookies

    return Response(**response_payload)


def basic_html(code=None, content_type=None, headers=None, cookies=None):
    # username will eventually come from app
    def inner(func):
        print(f"Basic HTML Response code {code}")

        def wrapper(*args, **kwargs):
            body = func(*args, **kwargs)
            return wrap_response(body, code, content_type, headers, cookies)

        return wrapper

    return inner
