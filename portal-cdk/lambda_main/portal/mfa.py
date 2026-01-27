"""
For information on MFA reset mechanics, see docs/mfa_reset_workflow.png

/mfa -> /mfa/reset -> /mfa/return -> /reset-code

"""

import os
import random
import string

from util.responses import wrap_response
from util.format import render_template
from util.responses import form_body_to_dict
from util.cognito import (
    verify_user_password,
    set_mfa_reset_values,
    reset_user_mfa_with_password,
    get_cognito_user_attribute,
    sign_out_user,
    LOGOUT_URL,
)
from util import send_email
from util.auth import delete_cookies

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(child=True)

mfa_router = Router()

mfa_route = {
    "router": mfa_router,
    "prefix": "/mfa",
    "name": "MFA",
}


# Externally visibile primary host name
inbound_host = os.getenv("DEPLOYMENT_HOSTNAME")


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choices(characters, k=length))
    return random_string


def do_mfa_reset(username):
    # Set 10-char code
    mfa_reset_code = generate_random_string(10)
    set_mfa_reset_values(username, mfa_reset_code)
    return_url = (
        f"https://{inbound_host}/mfa/return?"
        f"mfa_reset_code={mfa_reset_code}&"
        f"username={username}"
    )

    cog_email = get_cognito_user_attribute(username, "email")
    logger.debug(f"User {username}'s email is {cog_email}")

    # Create email
    email_dict = {
        "to": {
            "email": [
                cog_email,
            ],
        },
        "html_body": (
            f"MFA Reset code is <code>{mfa_reset_code}</code>."
            "<hr>"
            f"<b>Click Here</b>: <a href={return_url}>{return_url}</a>"
        ),
        "subject": "OpenScienceLab MFA reset Code",
    }

    # Send email
    result, reason = send_email.send_user_email(email_dict)
    if result == "Error":
        logger.error(f"Email failed to send: {reason}")
        return False

    logger.info(f"MFA Email sent to {cog_email}")
    return True


@mfa_router.get("/", include_in_schema=False)
def root():
    req_content = render_template(
        name="mfa_reset_request.j2", input={"username": "", "warning": ""}, content=""
    )

    return wrap_response(
        render_template(
            content=req_content,
            title="OpenScienceLab - MFA Reset",
            name="logged-out.j2",
        )
    )


@mfa_router.post("/reset", include_in_schema=False)
def reset_post():
    form = form_body_to_dict(mfa_router.current_event.body)
    username = form.get("username")
    password = form.get("password")

    if not verify_user_password(username, password):
        req_content = render_template(
            name="mfa_reset_request.j2",
            input={"username": username, "warning": "Username or Password not found."},
            content="",
        )
    else:
        if not do_mfa_reset(username):
            warning = (
                "Could not send MFA Reset email, please email the OSL admins at "
                "<a href='mailto:uaf-jupyterhub-asf@alaska.edu'>uaf-jupyterhub-asf@alaska.edu</a>"
            )
            req_content = render_template(
                name="mfa_reset_request.j2",
                input={
                    "username": username,
                    "warning": warning,
                },
                content="",
            )
        else:
            req_content = "MFA Reset processed, check your email"

    return wrap_response(
        render_template(
            content=req_content,
            title="OpenScienceLab - MFA Reset",
            name="logged-out.j2",
        )
    )


@mfa_router.get("/return", include_in_schema=False)
def email_return():
    username = mfa_router.current_event.query_string_parameters.get("username")
    mfa_reset_code = mfa_router.current_event.query_string_parameters.get(
        "mfa_reset_code"
    )
    req_content = render_template(
        name="mfa_reset_return.j2",
        input={
            "username": username,
            "mfa_reset_code": mfa_reset_code,
            "warning": "",
        },
        content="",
    )

    return wrap_response(
        render_template(
            content=req_content,
            title="OpenScienceLab - MFA Reset",
            name="logged-out.j2",
        )
    )


@mfa_router.post("/reset-code", include_in_schema=False)
def reset_code_post():
    form = form_body_to_dict(mfa_router.current_event.body)
    username = form.get("username")
    password = form.get("password")
    mfa_reset_code = form.get("mfa_reset_code")

    if reset_user_mfa_with_password(username, password, mfa_reset_code):
        # Successful reset, delete users cookies and redirect to login
        logger.info(f"MFA successfully reset for {username}")

        # Log user out of their cognito session
        sign_out_user(username)

        # Confirm MFA Reset success
        return wrap_response(
                body=render_template(
                    content=render_template(
                        title="",
                        name="mfa_reset_success.j2",
                        content="",
                        input={"logout_url": LOGOUT_URL}
                    ),
                title="OpenScienceLab - MFA successfully reset",
                name="logged-out.j2",
            ),
            code=200,
            cookies=delete_cookies(),
        )

    # MFA Reset failed
    req_content = render_template(
        name="mfa_reset_return.j2",
        input={
            "username": username,
            "mfa_reset_code": mfa_reset_code,
            "warning": (
                "Error resetting MFA. Please verify username, "
                "password and reset code."
            ),
        },
        content="",
    )

    return wrap_response(
        render_template(
            content=req_content,
            title="OpenScienceLab - MFA Reset",
            name="logged-out.j2",
        )
    )
