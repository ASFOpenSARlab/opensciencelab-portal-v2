from util.format import (
    portal_template,
)
from util.auth import require_access
from util.session import current_session
from util.user import User
from util.responses import wrap_response
from pathlib import Path
import json
from base64 import b64decode
from urllib.parse import urlencode, parse_qs
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


def enforce_profile_access():
    def inner(func):
        def wrapper(*args, **kwargs):
            username = current_session.auth.cognito.username
            user = User(username=username)

            if "admin" in user.access:
                # If admin, continue to return normally
                return func(*args, **kwargs)
            elif "user" in user.access:
                # If user role, check if username is their own
                if kwargs["username"] != username:
                    # If username not filled correctly, redirect to matching username
                    next_url = f"/portal/profile/form/{username}"
                    return wrap_response(
                        body={f"Redirect to {next_url}"},
                        code=302,
                        headers={"Location": next_url},
                    )
                # If user is correct, continue to page
                return func(*args, **kwargs)
            else:
                # Log error if user does not have a covered access type
                logger.error(
                    f"{username} does not have covered access type. User access: {user.access}"
                )

            next_url = "/portal"
            return wrap_response(
                body={f"Redirect to {next_url}"},
                code=302,
                headers={"Location": next_url},
            )

        return wrapper

    return inner


# This catches "/portal/profile", but "/portal/profile" is uncatchable
@profile_router.get("")
@require_access()
def profile_root():
    username = current_session.user.username
    return wrap_response(
        body="Redirecting to User Profile",
        headers={"Location": f"/portal/profile/form/{username}"},
        code=302,
    )


@profile_router.get("/form/bob")
@require_access()
@portal_template()
def profile_bob():
    page_components = {"input": {}, "content": "Profile Bob"}
    username = current_session.auth.cognito.username
    if username != "bob":
        page_components["content"] = "You are <b>NOT</b> Bob!"

    return page_components


@profile_router.get("/form/<username>")
@require_access()
@enforce_profile_access()
@portal_template(name="profile.j2")
def profile_user(username: str):
    page_dict = {
        "content": f"Profile for user {username}",
        "input": {
            "username": username,
            "default_value": "Choose...",
            "warning_missing": "Value is missing",
        },
    }

    CWD = Path(__file__).parent.resolve().absolute()
    with open(CWD / "../data/countries.json", "r") as f:
        page_dict["input"]["countries"] = json.loads(f.read())

    # Get query string if present
    query_params = profile_router.current_event.query_string_parameters

    # Set profile based on saved user profile or query_params if present
    profile = None
    if query_params:
        profile = query_params
    else:
        user_class = User(username=username)
        if user_class:
            if hasattr(user_class, "profile"):
                profile = user_class.profile

    # Append profile to page_dict and return
    if profile:
        page_dict["input"]["profile"] = profile
    return page_dict


def validate_profile_dict(query_dict: dict) -> tuple[bool, dict[str, str]]:
    correct = True
    errors = {}

    # Country Errors
    if query_dict["country_of_residence"] == "default":
        correct = False
        errors["country_of_residence_error"] = "missing"

    # NASA relation Errors
    if query_dict["is_affiliated_with_nasa"] == "default":
        correct = False
        errors["is_affiliated_with_nasa_error"] = "missing"

    if query_dict["is_affiliated_with_nasa"] == "yes":
        if query_dict["user_or_pi_nasa_email"] == "default":
            correct = False
            errors["user_or_pi_nasa_email_error"] = "missing"

        if (
            query_dict["user_or_pi_nasa_email"] == "yes"
            and query_dict["user_affliated_with_nasa_research_email"] == ""
        ):
            correct = False
            errors["user_affliated_with_nasa_research_email_error"] = "missing"

        if (
            query_dict["user_or_pi_nasa_email"] == "no"
            and query_dict["pi_affliated_with_nasa_research_email"] == ""
        ):
            correct = False
            errors["pi_affliated_with_nasa_research_email_error"] = "missing"

    # US GOV relation Errors
    if query_dict["is_affiliated_with_us_gov_research"] == "default":
        correct = False
        errors["is_affiliated_with_us_gov_research_error"] = "missing"

    if (
        query_dict["is_affiliated_with_us_gov_research"] == "yes"
        and query_dict["user_affliated_with_gov_research_email"] == ""
    ):
        correct = False
        errors["user_affliated_with_gov_research_email_error"] = "missing"

    # ISRO relation Errors
    if query_dict["is_affliated_with_isro_research"] == "default":
        correct = False
        errors["is_affliated_with_isro_research_error"] = "missing"

    if (
        query_dict["is_affliated_with_isro_research"] == "yes"
        and query_dict["user_affliated_with_isro_research_email"] == ""
    ):
        correct = False
        errors["user_affliated_with_isro_research_email_error"] = "missing"

    # University relation Errors
    if query_dict["is_affliated_with_university"] == "default":
        correct = False
        errors["is_affliated_with_university_error"] = "missing"

    return correct, errors


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
    correct, errors = validate_profile_dict(query_dict)

    # Format checkboxes to boolean values
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

    # Redirect to profile if not filled out correctly, pass provided values as well for form repopulation
    if not correct:
        errors.update(query_dict)
        return False, errors

    # Return dictionary of values
    return True, query_dict


@profile_router.post("/form/<username>")
@require_access()
@enforce_profile_access()
def profile_user_filled(username: str):
    # Parse form request
    body = profile_router.current_event.body
    success, query_dict = process_profile_form(body)

    # Redirect based on if the form was successfully parsed
    if success:
        # query_dict must be profile values at this point
        # Update user profile
        user = User(username)
        user.profile = query_dict
        # Update require user access
        user.require_profile_update = False

        # Send the user to the portal
        next_url = "/portal"
        return wrap_response(
            body={f"Redirect to {next_url}"},
            code=302,
            headers={"Location": next_url},
        )

    # query_dict must be form data and errors at this point
    query_string = urlencode(query_dict)
    # Send the user back to the profile page
    next_url = f"/portal/profile/form/{username}?{query_string}"
    return wrap_response(
        body={f"Redirect to {next_url}"},
        code=302,
        headers={"Location": next_url},
    )
