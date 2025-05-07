from aws_lambda_powertools.event_handler import (
    Response,
    content_types,
)


def basic_html(
    code=200, content_type=content_types.TEXT_HTML, headers=None, cookies=None
):
    # username will eventually come from app
    def inner(func):
        print(f"Basic HTML Response code {code}")

        def wrapper(*args, **kwargs):
            body = func(*args, **kwargs)

            response_payload = {
                "status_code": code,
                "content_type": content_type,
                "body": body,
            }

            if headers:
                response_payload["headers"] = headers
            if cookies:
                response_payload["cookies"] = cookies

            return Response(**response_payload)

        return wrapper

    return inner
