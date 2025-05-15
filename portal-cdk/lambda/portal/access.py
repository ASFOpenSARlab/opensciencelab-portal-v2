from util.format import portal_template
from util.auth import require_access

from aws_lambda_powertools.event_handler.api_gateway import Router

access_router = Router()

access_route = {
    "router": access_router,
    "prefix": "/portal/access",
    "name": "Access",
}


# This catches "/portal/access"
@access_router.get("")
@require_access()
@portal_template(access_router)
def access_root():
    return "List All Labs"


@access_router.get("/add_lab")
@require_access()
@portal_template(access_router)
def add_lab():
    return "Create New Lab"


@access_router.get("/lab/<lab>")
@require_access()
@portal_template(access_router)
def view_lab(lab):
    return f"inspect lab {lab}"
