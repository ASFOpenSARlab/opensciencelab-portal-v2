

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("OSL Portal V2"),
    autoescape=select_autoescape()
)

IMPORT_PATH = 'https://opensciencelab.asf.alaska.edu/portal/hub/static/css/'

NAV_BAR_OPTIONS = [
    {
        "visible": True,
        "path": "/",
        "title": "Home",
    },
    {
        "visible": True,
        "path": "/token",
        "title": "Token",
    },
    {
        "visible": True,
        "path": "/admin",
        "title": "Admin",
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

def portal_template( content, username="Unknown"):

    template_input = {
        "content": content,
        "import_path": IMPORT_PATH,
        "nav_bar_options": NAV_BAR_OPTIONS,
        "username": username,
    }

    template = env.get_template("templates/main.j2")
    return template.render(**template_input)
