from objs.lab import Lab
from data import ALL_COUNTRIES, RESTRICTED_COUNTRIES


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

    if status == "approved":
        # Grant access w/ default profiles
        lab_obj.grant_user_access(username)
        # Welcome Email Here

    elif status == "rejected":
        # Send rejection email here
        pass

    elif status == "returned":
        # Send returned email here
        pass
