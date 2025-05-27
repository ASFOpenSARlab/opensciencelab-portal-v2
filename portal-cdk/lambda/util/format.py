import json
import os
import ast

from util.responses import wrap_response
from util.session import current_session
from util.auth import LOGIN_URL, LOGOUT_URL

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from aws_lambda_powertools import Logger

logger = Logger(child=True)

# Get current file location template loading
absolute_path = os.path.abspath(__file__)
current_directory = os.path.dirname(absolute_path)

ENV = Environment(
    loader=FileSystemLoader(f"{current_directory}/../templates/"),
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


def render_template(content, name=None, title="OSL Portal"):
    # App will be used later to generate template input

    # Check for a logged-out return path
    current_event = current_session.app.current_event
    return_path = current_event.query_string_parameters.get("return", None)
    logger.debug("return param is %s", return_path)

    if not name:
        name = "main.j2"

    username = current_session.auth.cognito.username

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


def portal_template(name=None, title=None, response=200):
    # I don't love response here
    def inner(func):
        def wrapper(*args, **kwargs):
            content = func(*args, **kwargs)

            body = render_template(name=name, content=content, title=title)

            if response:
                # If we received basic_response_code, return a basic_html response
                return wrap_response(body=body, code=response)

            return body

        return wrapper

    return inner


def request_context_string(app):
    context_string = f"{current_session.app.current_event.request_context}"
    context_ojb = ast.literal_eval(context_string)
    return json.dumps(context_ojb, indent=4, default=str)
