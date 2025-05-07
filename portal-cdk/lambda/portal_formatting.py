from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from aws_lambda_powertools.event_handler import (
    Response,
    content_types,
)

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


def basic_html(body, code=200, content_type=content_types.TEXT_HTML):
    return Response(
        status_code=code,
        content_type=content_type,
        body=body,
        # headers=custom_headers,
        # cookies=[Cookie(name="session_id", value="12345")],
    )


def portal_template(content, title="OSL Portal", username="Unknown"):
    template_input = {
        "content": content,
        "nav_bar_options": NAV_BAR_OPTIONS,
        "username": username,
        "title": title,
    }

    template = ENV.get_template("main.j2")
    return template.render(**template_input)
