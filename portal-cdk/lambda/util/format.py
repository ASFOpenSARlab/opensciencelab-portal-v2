import json
import ast

from util.responses import wrap_response
from util.session import current_session
from util.auth import LOGIN_URL, LOGOUT_URL, get_user_from_event

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from aws_lambda_powertools import Logger

logger = Logger(service="APP")

ENV = Environment(
    loader=FileSystemLoader("./templates/"),
    autoescape=select_autoescape(),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

NAV_BAR_OPTIONS = [
    {
        "visible": True,
        "path": "/portal",
        "title": "Home",
    },
    {
        "visible": True,
        "path": "/portal/profile",
        "title": "Profile",
    },
    {
        "visible": True,
        "path": "/portal/access",
        "title": "Access",
    },
    {
        "visible": True,
        "path": "/change_pass",
        "title": "Change Password",
    },
    {
        "visible": True,
        "path": "/set_mfa",
        "title": "Configure New MFA Device",
    },
    {
        "visible": True,
        "path": "/set_mfa",
        "title": "Authorize Users",
    },
]


def render_template(app, content, name=None, title="OSL Portal", username=None):
    # App will be used later to generate template input

    # Check for a logged-out return path
    return_path = app.current_event.query_string_parameters.get("return", None)
    logger.debug("return param is %s", return_path)

    if not name:
        name = "main.j2"

    if not username:
        username = current_session.auth.cognito.username

    logger.info(f"Username is {current_session.auth.cognito.username}")
    logger.info(f"cognito is {current_session.auth.cognito}")

    template_input = {
        "content": content,
        "nav_bar_options": NAV_BAR_OPTIONS,
        "username": username,
        "title": title,
        "login_url": LOGIN_URL,
        "logout_url": LOGOUT_URL,
        "return_path": f"&state={return_path}" if return_path else "",
    }

    template = ENV.get_template(name)

    return template.render(**template_input)


def portal_template(app, name=None, title=None, username=None, response=200):
    # username will eventually come from app
    # I don't love response here
    def inner(func):
        def wrapper(*args, **kwargs):
            content = func(*args, **kwargs)

            body = render_template(
                app, name=name, content=content, title=title, username=username
            )

            if response:
                # If we received basic_response_code, return a basic_html response
                return wrap_response(body=body, code=response)

            return body

        return wrapper

    return inner


def request_context_string(app):
    context_string = f"{app.current_event.request_context}"
    context_ojb = ast.literal_eval(context_string)
    return json.dumps(context_ojb, indent=4, default=str)
