from util.format import (
    portal_template,
)
from util.auth import require_access
from util.user.dynamo_db import get_all_items
from util.format import jinja_template

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(service="APP", level="DEBUG")

users_router = Router()

users_route = {
    "router": users_router,
    "prefix": "/portal/users",
    "name": "Users",
}


@users_router.get("")
@require_access("admin")
@portal_template()
def profile_root():
    # Fetch all users
    all_users = get_all_items()
    all_users_sorted = sorted(all_users, key=lambda x: x["username"])
    template_input = {"all_users_sorted": all_users_sorted}

    # Generate an HTML table
    return jinja_template(template_input, "user-table.j2")
