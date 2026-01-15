
from util.notifications import get_notes
from util.format import portal_template
from util.auth import require_access

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(service="APP", level="DEBUG")

notifications_router = Router()

notifications_route = {
    "router": notifications_router,
    "prefix": "/portal/notifications",
    "name": "Notifications",
}

@notifications_router.get("/<calendar>", include_in_schema=False)
@require_access(human=True)
# @portal_template()
def get_notifications(calendar) -> str:
  
    return "Something"