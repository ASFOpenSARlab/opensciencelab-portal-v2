from portal.responses import wrap_response

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

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


def portal_template(
    app, name="main.j2", title="OSL Portal", username="Unknown", response=200
):
    # username will eventually come from app
    # I don't love response here
    def inner(func):
        print(f"Loading Template {name}")

        def wrapper(*args, **kwargs):
            content = func(*args, **kwargs)

            template_input = {
                "content": content,
                "nav_bar_options": NAV_BAR_OPTIONS,
                "username": username,
                "title": title,
            }

            template = ENV.get_template(name)
            if response:
                # If we received basic_response_code, return a basic_html response
                body = template.render(**template_input)
                return wrap_response(body=body, code=response)

            return template.render(**template_input)

        return wrapper

    return inner
