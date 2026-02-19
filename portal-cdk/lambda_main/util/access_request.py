from aws_lambda_powertools import Logger
from data import ALL_COUNTRIES, RESTRICTED_COUNTRIES
from util.labs import LAB_CONFIGS
from objs.lab import Lab
from objs.user import User

from util.send_email import send_user_email

logger = Logger(child=True)


def compile_user_access_requests(user_profile, user_logged_in):
    access_requests = user_profile.get_requests()
    access_request_questions = {}

    if not access_requests:
        return access_requests, access_request_questions

    for request in access_requests:
        # Filter out "submission_*" fields for non-admins
        if not user_logged_in.is_admin():
            remove_keys = []
            for answer in request["answers"][-1].keys():
                if answer.startswith("submission"):
                    remove_keys.append(answer)
            for answer in remove_keys:
                del request["answers"][-1][answer]

        # Capture full text of questions
        lab_obj = Lab(request["labname"])
        access_request_questions[request["labname"]] = (
            lab_obj.access_request_questions()
        )
        request["lab_friendly_name"] = lab_obj.get_lab_config().friendly_name

    return access_requests, access_request_questions


def get_country_list() -> dict:
    return ALL_COUNTRIES


def restricted_countries_html_color(restrictions: list) -> str:
    if 2 in restrictions and 3 in restrictions:
        return "#F73B3B"  # Very Red
    if 2 in restrictions or 3 in restrictions:
        return "#F76060"  # Red
    if 1 in restrictions and 4 in restrictions:
        return "#F7ED14"  # Very Yellow
    return "#F7F16A"  # Yellow


def get_restricted_countries():
    """
    Create color-coded dictionary of country restrictions

    Returns:
        {
           'AF': {'name': 'Afghanistan', 'restrictions': [3], 'color': '#F7F16A'},
           ....
        }
    """
    return {
        c: d | {"color": restricted_countries_html_color(d["restrictions"])}
        for c, d in RESTRICTED_COUNTRIES.items()
    }


def request_status_change_action(lab_obj, username: str, status: str):
    """

    Perform actions based on access request status change

    Args:
        username: User whose status has changes
        status: New status

    Returns:

    """

    update_email = {
        "to": {"username": username},
        "from": {username: "osl-admin"},
        "subject": f"OpenScienceLab Access Application {status[0].upper() + status[1:]}",
        "html_body": "You should never see this message...",
    }

    lab_name = LAB_CONFIGS[lab_obj.labname].friendly_name

    if status == "approved":
        # Grant access w/ default profiles
        lab_obj.grant_user_access(username)
        logger.info(f"granted {username} access to {lab_obj.labname}")

        update_email["html_body"] = (
            f"Hello {username},<br><br>"
            f"Your access to the <b>{lab_name}</b> deployment of OpenScienceLab has been approved.<br><br>"
            "This access is month-to-month and as-budget-allows. If your access is set to be revoked,<br>"
            "we will get in touch to ensure that you are able to download any workflows and results<br>"
            "before you lose access.<br>"
            "If you have any questions or concerns, please do not hesitate to contact us at "
            "uaf-jupyterhub-admin@alaska.edu.<br><br>"
            "The OpenScienceLab Admin Team"
        )

    elif status == "rejected":
        # Send rejection email here
        update_email["html_body"] = (
            f"Hello {username},<br><br>"
            f"We are unable to complete your request for access to <b>{lab_name}</b> at this time.<br><br>"
            "We apologize for this inconvenience.<br><br>"
            "The OpenScienceLab Admin Team"
        )

    elif status == "returned":
        # Send returned email here
        update_email["html_body"] = (
            f"Hello {username},<br><br>"
            f"Your application for access to <b>{lab_name}</b> has been returned.<br><br>"
            "This may be due to lack of information to enable OpenScienceLab admins to "
            "make a decision. Please update your application to ensure all the questions "
            "are answered to your full ability and reapply.<br><br>"
            "The OpenScienceLab Admin Team"
        )

    result, reason = send_user_email(update_email)

    if result == "Error":
        logger.error(f"Application response email failed to send: {reason}")


def process_access_token(token_value: str, username: str) -> list:
    access_granted = []
    for labname, lab_config in LAB_CONFIGS.items():
        if lab_config.allows_tokens:
            lab = Lab(labname)
            for lab_token in lab.get_valid_access_tokens():
                if token_value in lab_token:
                    # Get user
                    user = User(username)

                    # Check if user has used the token
                    if user.check_used_token(token_value):
                        # Can't re-use a token
                        logger.warning(
                            f"User {username} tried to reuse token {token_value}"
                        )
                        continue

                    # Record token was applied
                    user.use_token(labname, token_value)

                    # Determine which profiles are granted
                    profiles = lab_token[token_value]

                    # Apply granted access
                    lab.grant_user_access(username, profiles=profiles)
                    access_granted.append(labname)
                    logger.info(
                        f"User {username} granted access to {labname} by token {token_value}"
                    )

    if not access_granted:
        logger.warning(f"User {username} tried to use invalid token '{token_value}'")

    return access_granted
