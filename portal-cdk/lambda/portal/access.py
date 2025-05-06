from portal_formatting import portal_template, basic_html

from aws_lambda_powertools.event_handler.api_gateway import Router

access_router = Router()

access_route = {
    "router": access_router,
    "prefix": "/portal/access",
    "name": "Access",
}


# This catches "/portal/access"
@access_router.get("")
def access_root():
    return basic_html(portal_template("List All Labs"))


@access_router.get("/add_lab")
def add_lab():
    return basic_html(portal_template("Create New Lab"))


@access_router.get("/lab/<lab>")
def view_lab(lab):
    return basic_html(portal_template(f"inspect lab {lab}"))
