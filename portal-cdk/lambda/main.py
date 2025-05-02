"""AWS Lambda function to handle HTTP requests and return formatted HTML responses."""

import json
import os

# https://docs.python.org/3/library/http.html
from http import HTTPStatus
import datetime

from portal_formatting import portal_template, basic_html

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.shared.cookies import Cookie
from aws_lambda_powertools.utilities import parameters

logger = Logger(service="APP")

TEMP_USERNAME = "emlundell"


def encrypt_data(data: dict) -> str:
    try:
        logger.info("INSIDE encrypt_data.....")
        secret_name = os.getenv("SSO_TOKEN_SECRET_NAME")
        sso_token = parameters.get_secret(secret_name)
        logger.info(sso_token[0:10])

        from opensarlab.auth import encryptedjwt

        data = encryptedjwt.encrypt(data, sso_token=sso_token)
    except Exception as e:
        logger.error(f"encrypt_data error: {e}")
        data = None
    return data


# Rest is V1, HTTP is V2
app = APIGatewayHttpResolver()


@app.get("/hello/<name>")
def hello_name(name):
    logger.info(f"Request from {name} received")
    return basic_html(portal_template(f"hello {name}!"))


@app.get("/hello")
def hello():
    logger.info("Request from unknown received")
    return basic_html(portal_template("Hello Unknown"))


@app.get("/")
def root():
    logger.info("The root of the carrot")
    return {"message": "hello there!!!!"}


@app.get("/portal/hub/auth")
def get_portal_hub_auth():
    # /portal/hub/auth?next_url=%2Flab%2Fsmce-test-opensarlab%2Fhub%2Fhome
    next_url = app.current_event.query_string_parameters.get("next_url", None)
    logger.info(f"GET auth: {next_url=}")
    return Response(
        status_code=HTTPStatus.FOUND.value,  # 302
        headers={
            "Location": next_url,
        },
    )


@app.post("/portal/hub/auth")
def post_portal_hub_auth():
    logger.info("Request user info")
    data = {
        "admin": True,
        "roles": ["user", "admin"],
        "name": f"{TEMP_USERNAME}",
        "has_2fa": 1,
        "force_user_profile_update": False,
        "ip_country_status": "unrestricted",
        "country_code": "US",
        "lab_access": {
            "smce-test-opensarlab": {
                "lab_profiles": ["m6a.large"],
                "time_quota": None,
                "lab_country_status": "unrestricted",
                "can_user_access_lab": True,
                "can_user_see_lab_card": True,
            },
        },
    }
    encrypted_data = encrypt_data(data)
    body = json.dumps({"data": encrypted_data, "message": "OK"})
    return Response(
        status_code=HTTPStatus.OK.value,  # 200
        body=body,
    )


@app.get("/portal/hub/login")
def portal_hub_login():
    logger.info("Log in user")
    cookie_name = "portal-username"
    cookie_value = encrypt_data(TEMP_USERNAME)
    expiration_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=7
    )
    portal_username_cookie = Cookie(
        name=cookie_name,
        value=cookie_value,
        path="/",
        secure=False,
        http_only=True,
        expires=expiration_date,
    )
    return Response(
        status_code=HTTPStatus.OK.value,  # 200
        content_type=content_types.TEXT_HTML,
        body="<html><body><p>hello</p></body></html>",
        cookies=[portal_username_cookie],
    )


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=True,
)
def lambda_handler(event, context):
    # print(json.dumps({"Event": event, "Context": context}, default=str))
    return app.resolve(event, context)
