from util.format import portal_template
from util.notifications import get_notifications
from util.auth import require_access

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(service="APP", level="DEBUG")

notifications_router = Router()

notifications_route = {
    "router": notifications_router,
    "prefix": "",
    "name": "Notifications",
}

@notifications_router.get("/user/notifications/<scope>", include_in_schema=False)
def notifications_deprecated(scope) -> str:
    query_params = notifications_router.current_event.query_string_parameters

    return get_notifications(scope, query_params.get("profile", None))

@notifications_router.get("/notifications/<scope>", include_in_schema=False)
# @portal_template()
def notifications(scope) -> str:
    query_params = notifications_router.current_event.query_string_parameters

    return get_notifications(scope, query_params.get("tag", None))