import datetime

import json
import base64

from util import swagger
from util import send_email
from util.responses import wrap_response
from util.format import portal_template, request_context_string
from util.auth import encrypt_data, require_access
from util.session import current_session
from util.user import User

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.shared.cookies import Cookie

hub_router = Router()

TEMP_USERNAME = "tester1"
COOKIE_NAME = "portal-username"

hub_route = {
    "router": hub_router,
    "prefix": "/portal/hub",
    "name": "Hub",
}

logger = Logger(child=True)


@hub_router.get("/", include_in_schema=False)
@require_access(human=True)
@portal_template()
def portal_hub_root():
    return "<h4>Hello</h4>"


@hub_router.get("/home", include_in_schema=False)
def portal_hub_home():
    home_root = "/portal"
    return wrap_response(
        body={"Redirect": home_root},
        code=302,
        content_type=content_types.APPLICATION_JSON,
        headers={"Location": home_root},
    )


@hub_router.get("/auth", include_in_schema=False)
@require_access(human=True)
def get_portal_hub_auth():
    # /portal/hub/auth?next_url=%2Flab%2Fsmce-test-opensarlab%2Fhub%2Fhome
    next_url = hub_router.current_event.query_string_parameters.get("next_url", None)
    username = current_session.auth.cognito.username
    logger.info(f"GET auth: {next_url=}, (username = {username}")

    ### Authenticate with Portal server cookie here
    # If not authenticated, go to /portal/hub/login so the user can authenticate within browser

    return wrap_response(
        body={"Redirect": next_url},
        code=302,
        content_type=content_types.APPLICATION_JSON,
        headers={"Location": next_url},
    )


@hub_router.post(
    "/auth",
    description="""
Returns an encrypted user profile, used by labs to validate users. 

<hr>

`POST` payload should be a base64 encoded JSON dictionary with a `username` key 
containing the username of the profile being validated.
    """,
    response_description="A dict containing encrypted profile information for a user.",
    responses={
        **swagger.format_response(
            example={
                "data": {
                    "admin": False,
                    "roles": ["user"],
                    "name": "<username>",
                    "has_2fa": True,
                    "force_user_profile_update": False,
                    "ip_country_status": "unrestricted",
                    "country_code": "US",
                    "lab_access": [],
                },
                "message": "OK",
            },
            description="Returns an encrypted user profile, used by labs to validate users.",
            code=200,
        ),
        **swagger.code_404_user_not_found,
    },
    tags=[hub_route["name"]],
)
def post_portal_hub_auth():
    post_data = hub_router.current_event.body
    post_data_decoded = json.loads(base64.b64decode(post_data).decode("utf-8"))
    username = post_data_decoded["username"]
    logger.info(f"Request user info = {username=}")

    user = User(username=username, create_if_missing=False)

    data = {
        "admin": user.is_admin(),
        "roles": user.access,
        "name": f"{username}",
        "has_2fa": True,
        "force_user_profile_update": user.require_profile_update,
        "ip_country_status": "unrestricted",
        "country_code": user.profile["country_of_residence"],
        "lab_access": user.labs,
    }
    encrypted_data = encrypt_data(data)

    return wrap_response(
        body=json.dumps({"data": encrypted_data, "message": "OK"}),
        code=200,
        content_type=content_types.APPLICATION_JSON,
    )


@hub_router.get("/login", include_in_schema=False)
@require_access(human=True)
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


swagger_email_options = {
    "response_description": "A dict containing if it's successful.",
    "responses": {
        **swagger.code_200_result_success,
        **swagger.code_403,
        # And other codes, when actually implementing this.
        # (If *one* user in list is invalid, do we email the others?)
    },
    "tags": ["Email"],
}


@hub_router.post(
    "/user/email",
    **swagger_email_options,
    description="""
Sends emails as defined in payload via SES. To help facilitate ease of use, usernames can be used instead of email addresses.
    
- If an username is given, user's email address on file is used
- As a special case, username "osl-admin" substitutes the admin email as defined in the portal config
- TO username and email are included for backward compatibility. TO will be defined by the SES_EMAIL.

<hr>
    
Format of `POST` payload should be a dict of the form:

```json
{
    "to": {
        "username": ["",] | "",
        "email": ["",] | ""
    },
    "from": {
        "username": "",
        "email": ""
    },
    "cc": {
        "username": ["",] | "",
        "email": ["",] | ""
    },
    "bcc": {
        "username": ["",] | "",
        "email": ["",] | ""
    },
    "subject": "",
    "html_body": "<message>"
}
```
""",
)
def send_user_email():
    request_data = hub_router.current_event.body

    result: str = send_email.send_user_email(request_data)

    return wrap_response(
        body=json.dumps({"result": result}),
        code=200 if result == "Success" else 422,
        content_type=content_types.APPLICATION_JSON,
    )
