import datetime
import os
import json

from util.responses import wrap_response, basic_json
from util.format import portal_template, request_context_string

from opensarlab.auth import encryptedjwt

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.shared.cookies import Cookie

hub_router = Router()

TEMP_USERNAME = "tester1"
COOKIE_NAME = "portal-username"

hub_route = {
    "router": hub_router,
    "prefix": "/portal/hub",
}

logger = Logger(service="APP")


def encrypt_data(data: dict | str) -> str:
    secret_name = os.getenv("SSO_TOKEN_SECRET_NAME")
    sso_token = parameters.get_secret(secret_name)

    # TODO: Fix initial code build time
    # The module `encryptedjwt`` uses the cryptography module which in turn uses Fernet
    # On a cold lambda start, Fernet takes at least 1 second to do it's thing
    # A warm lambda is nearly instant. Is there a pip wheel being build when cold?
    data = encryptedjwt.encrypt(data, sso_token=sso_token)
    return data


@hub_router.get("/")
@portal_template(hub_router)
def portal_hub_root():
    return "<h4>Hello</h4>"


@hub_router.get("/auth")
def get_portal_hub_auth():
    # /portal/hub/auth?next_url=%2Flab%2Fsmce-test-opensarlab%2Fhub%2Fhome
    next_url = hub_router.current_event.query_string_parameters.get("next_url", None)
    logger.info(f"GET auth: {next_url=}")

    ### Authenticate with Portal server cookie here
    # If not authenticated, go to /portal/hub/login so the user can authenticate within browser

    return wrap_response(
        body={"Redirect": next_url},
        code=302,
        content_type=content_types.APPLICATION_JSON,
        headers={"Location": next_url},
    )


@hub_router.post("/auth")
@basic_json()
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
    return json.dumps({"data": encrypted_data, "message": "OK"})


@hub_router.get("/login")
def portal_hub_login():
    try:
        logger.info("Log in user")

        ## Create portal-auth server cookie here

        ## Create portal-username browser cookie
        cookie_value = encrypt_data(TEMP_USERNAME)
        expiration_date = datetime.datetime.now(
            datetime.timezone.utc
        ) + datetime.timedelta(days=7)
        portal_username_cookie = Cookie(
            name=COOKIE_NAME,
            value=cookie_value,
            path="/",
            secure=False,
            http_only=True,
            expires=expiration_date,
        )

        return wrap_response(
            body="<html><body><p>hello - Cookie Created</p></body></html>",
            cookies=[portal_username_cookie],
        )

    except Exception as e:
        body = f"""
        <html><body>
        <h3>Error: @ '{hub_router.current_event.request_context.http.path}'</h3>
        <hr>
        <pre>{e}</pre>
        <hr>
        <pre>{request_context_string(hub_router)}</pre>
        </body></html>
        """
        return wrap_response(body=body, code=400)
