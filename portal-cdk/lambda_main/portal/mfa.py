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
)
from util import send_email

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

    # Create email
    email_dict = {
        "to": {
            "username": [
                username,
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
    send_email.send_user_email(email_dict)
    logger.info("Email sent")


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
        do_mfa_reset(username)
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
        logger.info(f"MFA successfully reset for {username}")
        req_content = (
            "MFA Reset Completed, <a href='/'>Log In</a> to configure your new MFA code"
        )
    else:
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
