from util.format import (
    portal_template,
)
from util.auth import require_access, get_user_from_event
from util.dynamo_db import update_item, get_item
from util.responses import wrap_response
from pathlib import Path
import json
from base64 import b64decode
from urllib.parse import parse_qs
from typing import Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(service="APP", level="DEBUG")

profile_router = Router()

profile_route = {
    "router": profile_router,
    "prefix": "/portal/profile",
    "name": "Profile",
}


# This catches "/portal/profile", but "/portal/profile" is uncatchable
@profile_router.get("")
@require_access()
@portal_template(profile_router)
def profile_root():
    page_components = {"input": {}, "content": "Profile Base 1"}
    return page_components


@profile_router.get("/bob")
@require_access()
@portal_template(profile_router)
def profile_bob():
    page_components = {"input": {}, "content": "Profile Bob"}
    username = get_user_from_event(profile_router)
    if username != "bob":
        page_components["contents"] = "You are <b>NOT</b> Bob!"
        return "You are <b>NOT</b> Bob!"

    return page_components


@profile_router.get("/<user>")
@require_access()
@portal_template(profile_router, name="profile.j2")
def profile_user(user):
    page_dict = {
        "content": f"Profile for user {user}",
        "input": {
            "default_value": "Choose...",
        },
    }

    CWD = Path(__file__).parent.resolve().absolute()
    with open(CWD / "../data/countries.json", "r") as f:
        page_dict["input"]["countries"] = json.loads(f.read())

    user_dict = get_item(user)
    if user_dict:
        if user_dict["profile"]:
            page_dict["input"]["profile"] = user_dict["profile"]

    return page_dict


def process_profile_form(request_body: str) -> tuple[bool, dict[str, Any]]:
    """Processes the profile form

    Args:
        request_body (str): Base64 encoded request body

    Returns:
        tuple[bool, dict[str, Any]]: _description_
    """
    decoded_body = b64decode(request_body)
    parsed_qs = parse_qs(decoded_body, keep_blank_values=True)
    query_dict: dict[str, Any] = {
        k.decode("utf-8"): v[0].decode("utf-8") for k, v in parsed_qs.items()
    }

    # Validate Form
    ## TODO
    correct = True
    if not correct:
        return False, {}

    ## Redirect to profile if not filled out correctly

    # Format checkboxes
    checkbox_fields = [
        "faculty_member_affliated_with_university",
        "research_member_affliated_with_university",
        "graduate_student_affliated_with_university",
    ]

    for field in checkbox_fields:
        if field in query_dict:
            query_dict[field] = True
        else:
            query_dict[field] = False

    # Format yes/no to Bool values
    for k, v in query_dict.items():
        if v == "yes":
            query_dict[k] = True
        if v == "no":
            query_dict[k] = False
        # If value is "default" then it should not be important at this stage since the form is validated
        if v == "default":
            query_dict[k] = False

    # Return dictionary of values
    return True, query_dict


@profile_router.post("/<user>")
@require_access()
def profile_user_filled(user):
    # Parse form request
    body = profile_router.current_event.body
    success, query_dict = process_profile_form(body)

    if success:
        # Update user profile
        update_item(user, {"profile": query_dict})

        # Send the user to the portal
        next_url = "/portal"
        return wrap_response(
            body={f"Redirect to {next_url}"},
            code=302,
            headers={"Location": next_url},
        )

    # Send the user back to the profile page
    next_url = "/portal/profile/<user>"
    return wrap_response(
        body={f"Redirect to {next_url}"},
        code=302,
        headers={"Location": next_url},
    )
