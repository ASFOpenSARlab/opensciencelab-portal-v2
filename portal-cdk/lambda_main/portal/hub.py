import datetime
import os

import json
import base64

import boto3

from util import swagger
from util.responses import wrap_response
from util.format import portal_template, request_context_string
from util.auth import encrypt_data, require_access, decrypt_data
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

_sesv2 = None


def get_sesv2() -> None:
    global _sesv2
    if not _sesv2:
        _sesv2 = boto3.client("sesv2")
    return _sesv2


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


def _get_user_email_for_username(username: str) -> str:
    if not username:
        return None

    # Since osl-admin is a special username, make sure we override with the admin email
    if username == "osl-admin":
        return os.getenv("SES_EMAIL")

    try:
        user = User(username, create_if_missing=False)
    except Exception:
        logger.error(f"User {username} not found")
        return None

    return user.email


def _parse_email_message(data: dict) -> dict:
    """
    Parse sent POST payload into a dictionary of email parameters

    Return dict of form:

    {
        "from": ["",],
        "to": ["",],
        "reply_to": ["",],
        "cc": ["",],
        "bcc": ["",],
        "subject": "",
        "html_body": ""
    }

    """

    email_meta = {}

    ####  To
    to_email = data["to"].get("email", [])
    if isinstance(to_email, str):
        to_email = [to_email]

    to_username = data["to"].get("username", [])
    if isinstance(to_username, str):
        to_username = [to_username]
    for user in to_username:
        user_email = _get_user_email_for_username(username=user)
        if user_email:
            to_email.append(user_email)

    if not to_email:
        raise Exception("No TO user specified")

    email_meta["to"] = to_email

    ####  CC
    cc = data.get("cc", None)
    if cc:
        cc_email = cc.get("email", [])
        if isinstance(cc_email, str):
            cc_email = [cc_email]

        cc_username = cc.get("username", [])
        if isinstance(cc_username, str):
            cc_username = [cc_username]
        for user in cc_username:
            user_email = _get_user_email_for_username(username=user)
            if user_email:
                cc_email.append(user_email)

        email_meta["cc"] = cc_email

    ####  BCC
    bcc = data.get("bcc", None)
    if bcc:
        bcc_email = bcc.get("email", [])
        if isinstance(bcc_email, str):
            bcc_email = [bcc_email]

        bcc_username = bcc.get("username", [])
        if isinstance(bcc_username, str):
            bcc_username = [bcc_username]

        for user in bcc_username:
            user_email = _get_user_email_for_username(username=user)
            if user_email:
                bcc_email.append(user_email)

        email_meta["bcc"] = bcc_email

    ####  FROM
    ## It will be assumed that all emails will be FROM only one user and one REPLY-TO.
    ## Therefore the FROM will always be overriden and all inputed FROM parameters will be ignored.
    email_meta["reply_to"] = [os.getenv("SES_EMAIL")]
    email_meta["from"] = f'"OpenScienceLab" <admin@{os.getenv("SES_DOMAIN")}>'

    #### subject
    data_subject = data.get("subject", "")
    if data_subject:
        email_meta["subject"] = data_subject

    data_body = data.get("html_body", "")

    if data_body:
        email_meta["html_body"] = f"""
        <html>
            <body>
                <h1> Message from OpenScienceLab </h1>
                <section>
                    {data_body}
                </section>
                <section>
                    <hr/>
                    <p> OpenScienceLab is operated by the Alaska Satellite Facility | <a href="https://opensarlab-docs.asf.alaska.edu">OpenScienceLab documentation</a>.</p>
                </section>
            </body>
        </html>
        """

    return email_meta


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
    sesv2: boto3.Client = get_sesv2()

    try:
        request_data = hub_router.current_event.body

        decrypted_data: dict = decrypt_data(request_data)

        parsed_data: dict = _parse_email_message(decrypted_data)

        sesv2.send_email(
            FromEmailAddress=parsed_data.get("from", ""),
            Destination={
                "ToAddresses": parsed_data.get("to", []),
                "CcAddresses": parsed_data.get("cc", []),
                "BccAddresses": parsed_data.get("bcc", []),
            },
            ReplyToAddresses=parsed_data.get("reply_to", []),
            Content={
                "Simple": {
                    "Subject": {
                        "Data": parsed_data.get("subject", ""),
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Html": {
                            "Data": parsed_data.get("html_body", ""),
                            "Charset": "UTF-8",
                        },
                    },
                },
            },
        )

        result = "Success"
    except Exception as e:
        logger.error(f"Could not send email: {e}")
        logger.info("Sending admin error email...")

        html_body = f"""
        <html>
            <body>
                <h1> Message from OpenScienceLab </h1>
                <section>
                    <p>There was an error while sending an email...</p>
                </section>
                <section>
                    {e}
                </section>
            </body>
        </html>
        """

        sesv2.send_email(
            FromEmailAddress=f'"OpenScienceLab" <admin@{os.getenv("SES_DOMAIN")}>',
            Destination={
                "ToAddresses": [os.getenv("SES_EMAIL")],
            },
            ReplyToAddresses=[os.getenv("SES_EMAIL")],
            Content={
                "Simple": {
                    "Subject": {
                        "Data": "Error in sending email",
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Html": {
                            "Data": html_body,
                            "Charset": "UTF-8",
                        },
                    },
                },
            },
        )

        result = "Error"

    return wrap_response(
        body=json.dumps({"result": result}),
        code=200 if result == "Success" else 422,
        content_type=content_types.APPLICATION_JSON,
    )
