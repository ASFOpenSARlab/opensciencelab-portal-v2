"""AWS Lambda function to handle HTTP requests and return formatted HTML responses."""

import json
import os
from http import HTTPStatus  # https://docs.python.org/3/library/http.html
import datetime

from opensarlab.auth import encryptedjwt

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.shared.cookies import Cookie
from aws_lambda_powertools.utilities import parameters

from portal import routes
from static import get_static_object
from portal_formatting import portal_template, basic_html

logger = Logger(service="APP")

TEMP_USERNAME = "tester1"


def decrypt_data(data: dict | str) -> str:
    secret_name = os.getenv("SSO_TOKEN_SECRET_NAME")
    sso_token = parameters.get_secret(secret_name)

    # TODO: Fix initial code build time
    # The module `encryptedjwt`` uses the cryptography module which in turn uses Fernet
    # On a cold lambda start, Fernet takes at least 1 second to do it's thing
    # A warm lambda is nearly instant. Is there a pip wheel being build when cold?
    data = encryptedjwt.decrypt(data, sso_token=sso_token)
    return data


def encrypt_data(data: dict | str) -> str:
    secret_name = os.getenv("SSO_TOKEN_SECRET_NAME")
    sso_token = parameters.get_secret(secret_name)

    # TODO: Fix initial code build time
    # The module `encryptedjwt`` uses the cryptography module which in turn uses Fernet
    # On a cold lambda start, Fernet takes at least 1 second to do it's thing
    # A warm lambda is nearly instant. Is there a pip wheel being build when cold?
    data = encryptedjwt.encrypt(data, sso_token=sso_token)
    return data


# Rest is V1, HTTP is V2
app = APIGatewayHttpResolver()

# Add portal routes
for prefix, router in routes.items():
    app.include_router(router, prefix=prefix)


@app.get("/")
def root():
    return basic_html(portal_template("Welcome to OpenScienceLab"))


@app.get("/login")
def login():
    return basic_html(portal_template("Add login form here."))


@app.get("/logout")
def logout():
    return basic_html(portal_template("You have been logged out"))


@app.get("/register")
def register():
    return basic_html(portal_template("Register a new user here"))


@app.get("/static/.+")
def static():
    logger.info("Path is %s", app.current_event.path)
    return get_static_object(app.current_event)


@app.not_found
def handle_not_found(error):
    body = f"""
    <h3>Not Found:</h3>
    <pre>{app.current_event.request_context}</pre>
    """

    return basic_html(portal_template(body))


@app.get("/")
def root():
    logger.info("The root of the carrot")
    return {"message": "hello there!!!!"}


@app.get("/portal/hub/auth")
def get_portal_hub_auth():
    # /portal/hub/auth?next_url=%2Flab%2Fsmce-test-opensarlab%2Fhub%2Fhome
    next_url = app.current_event.query_string_parameters.get("next_url", None)
    logger.info(f"GET auth: {next_url=}")

    ### Authenticate with Portal server cookie here
    # If not authenticated, go to /portal/hub/login so the user can authenticate within browser

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
    try:
        logger.info("Log in user")

        ## Create portal-auth server cookie here

        ## Create portal-username browser cookie
        cookie_name = "portal-username"
        cookie_value = encrypt_data(TEMP_USERNAME)
        expiration_date = datetime.datetime.now(
            datetime.timezone.utc
        ) + datetime.timedelta(days=7)
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
    except Exception as e:
        logger.error(f"Error inside /portal/hub/login {e}")
        return Response(
            body=f"<p>Error</p><p>{e}</p>",
            status_code=HTTPStatus.OK.value,
        )


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=True,
)
def lambda_handler(event, context):
    # print(json.dumps({"Event": event, "Context": context}, default=str))
    return app.resolve(event, context)
