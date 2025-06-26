import json
import os
import ast
import copy

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
        "visible": False,
        "path": "/portal/access",
        "title": "Access",
        "requires_admin": True,
    },
    {
        "visible": False,
        "path": "/change_pass",
        "title": "Change Password",
    },
    {
        "visible": False,
        "path": "/set_mfa",
        "title": "Configure New MFA Device",
    },
    {
        "visible": False,
        "path": "/set_mfa",
        "title": "Authorize Users",
    },
    {
        "visible": False,
        "path": "/portal/users",
        "title": "Manage Users",
        "requires_admin": True,
    },
]


def jinja_template(template_input, template_name):
    template = ENV.get_template(template_name)
    return template.render(**template_input)


def render_template(content, input=None, name=None, title="OSL Portal"):
    # Check for a logged-out return path
    current_event = current_session.app.current_event
    return_path = current_event.query_string_parameters.get("return", None)
    logger.debug("return param is %s", return_path)

    if not name:
        name = "main.j2"

    username = current_session.auth.cognito.username

    # Manage restrict access
    nav_bar_options = copy.deepcopy(NAV_BAR_OPTIONS)
    for option in nav_bar_options:
        if current_session.user and option.get("requires_admin"):
            if "admin" in current_session.user.access:
                option["visible"] = True

    # Create input dict for jinja formatting
    template_input = {
        "content": content,
        "nav_bar_options": nav_bar_options,
        "username": username,
        "title": title,
        "login_url": LOGIN_URL,
        "logout_url": LOGOUT_URL,
        "return_path": f"&state={return_path}" if return_path else "",
    }
    if input:
        template_input.update(input)

    return jinja_template(template_input, name)


def portal_template(name=None, title=None, response=200):
    # I don't love response here
    def inner(func):
        def wrapper(*args, **kwargs):
            # Dict for each value a page needs
            page_dict = {
                "content": "",
                "input": {},
                "name": name,
                "title": title,
            }

            # Get page info from function
            content = func(*args, **kwargs)

            # If return value is string, assume it is contents
            if isinstance(content, str):
                page_dict["content"] = content
            elif isinstance(content, dict):
                # Else if return value is dict, update page_dict with provided values
                page_dict.update(content)

            # Render page
            body = render_template(**page_dict)

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
