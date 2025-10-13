import traceback

from util.format import (
    portal_template,
)
from util.auth import require_access
from util.session import current_session
from util.user.dynamo_db import get_all_items
from util.format import jinja_template
from util.responses import wrap_response
from util.exceptions import CognitoError, DbError
from util.user import User
from util.user_ip_logs_stream import get_user_ip_logs

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(service="APP", level="DEBUG")

users_router = Router()

users_route = {
    "router": users_router,
    "prefix": "/portal/users",
    "name": "Users",
}


def _delete_user(username) -> bool:
    current_username = current_session.auth.cognito.username
    user_to_delete = User(username=username)

    if user_to_delete.is_admin():
        logger.warning(
            "%s attempted to delete admin user %s",
            current_username,
            user_to_delete.username,
        )
        return False

    try:
        user_to_delete.remove_user()
    except (CognitoError, DbError):
        logger.warning(
            "could not delete user %s",
            username,
        )
        return False

    return True


def _user_set_lock(username, lock: bool) -> bool:
    current_username = current_session.auth.cognito.username
    user_to_toggle = User(username=username)

    if user_to_toggle.is_admin():
        logger.warning(
            "%s attempted to %s admin user %s",
            current_username,
            "lock" if lock else "unlock",
            user_to_toggle.username,
        )
        return False
    user_to_toggle.is_locked = lock
    return True


@users_router.get("", include_in_schema=False)
@require_access("admin", human=True)
@portal_template()
def users_root():
    # See if we were redirected with a message:
    message = users_router.current_event.query_string_parameters.get("message")
    success = users_router.current_event.query_string_parameters.get("success", "false")
    username = users_router.current_event.query_string_parameters.get("username")

    # Fetch all users
    all_users = get_all_items()
    all_users_sorted = sorted(all_users, key=lambda x: x["username"])
    template_input = {
        "all_users_sorted": all_users_sorted,
        "message": message,
        "success": success.lower() == "true",
        "username": username,
    }

    # Generate an HTML table
    return jinja_template(template_input, "user-table.j2")


@users_router.post("/unlock/<username>", include_in_schema=False)
@require_access("admin", human=True)
def unlock_user(username):
    success = _user_set_lock(username, False)

    get_params = [
        f"username={username}",
        "message=unlocked",
        f"success={success}",
    ]

    return wrap_response(
        body="Post Unlock redirect",
        headers={"Location": f"/portal/users?{'&'.join(get_params)}"},
        code=302,
    )


@users_router.post("/lock/<username>", include_in_schema=False)
@require_access("admin", human=True)
def lock_user(username):
    success = _user_set_lock(username, True)

    get_params = [
        f"username={username}",
        "message=locked",
        f"success={success}",
    ]

    return wrap_response(
        body="Post Lock redirect",
        headers={"Location": f"/portal/users?{'&'.join(get_params)}"},
        code=302,
    )


@users_router.post("/delete/<username>", include_in_schema=False)
@require_access("admin", human=True)
def delete_user(username):
    success = _delete_user(username)

    get_params = [
        f"username={username}",
        "message=deleted",
        f"success={success}",
    ]

    return wrap_response(
        body="Post Delete redirect",
        headers={"Location": f"/portal/users?{'&'.join(get_params)}"},
        code=302,
    )


@users_router.get("/info", include_in_schema=True)
@require_access("admin", human=False)
def get_user_ip_info():
    username: str | None = users_router.current_event.query_string_parameters.get(
        "username", None
    )
    start_date: str | None = users_router.current_event.query_string_parameters.get(
        "starttime", None
    )
    end_date: str | None = users_router.current_event.query_string_parameters.get(
        "endtime", None
    )
    limit: str | None = users_router.current_event.query_string_parameters.get(
        "limit", None
    )

    try:
        results = get_user_ip_logs(
            username=username, start_date=start_date, end_date=end_date, limit=limit
        )
    except Exception:
        logger.error(traceback.print_exc())
        return wrap_response(
            body="Something went wrong with getting the User Info",
            code=422,
        )

    return wrap_response(
        body=results,
        code=200,
    )
