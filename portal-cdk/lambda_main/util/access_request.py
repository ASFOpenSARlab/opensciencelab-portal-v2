from pathlib import Path
import json

from objs.lab import Lab


RESTRICTED_COUNTRIES = {
    "AF": {"name": "Afghanistan", "restrictions": [3]},
    "BH": {"name": "Bahrain", "restrictions": [4]},
    "BY": {"name": "Belarus", "restrictions": [3, 4]},
    "BT": {"name": "Bhutan", "restrictions": [1]},
    "MM": {"name": "Burma", "restrictions": [3]},
    "KH": {"name": "Cambodia", "restrictions": [3]},
    "CT": {"name": "Central African Republic", "restrictions": [3]},
    "CN": {"name": "China, Peoples Republic", "restrictions": [3, 4]},
    "CD": {
        "name": "Congo (Formerly Zaire; Democratic Republic of)",
        "restrictions": [3],
    },
    "CU": {"name": "Cuba", "restrictions": [2, 3]},
    "CY": {"name": "Cyprus", "restrictions": [3]},
    "EG": {"name": "Egypt", "restrictions": [4]},
    "ER": {"name": "Eritrea", "restrictions": [3]},
    "ET": {"name": "Ethiopia", "restrictions": [3]},
    "HT": {"name": "Haiti", "restrictions": [3]},
    "IR": {"name": "Iran", "restrictions": [1, 2, 3, 4]},
    "IQ": {"name": "Iraq", "restrictions": [3, 4]},
    "IL": {"name": "Israel", "restrictions": [4]},
    "JO": {"name": "Jordan", "restrictions": [4]},
    "KP": {"name": "Korea, North", "restrictions": [1, 2, 3, 4]},
    "KW": {"name": "Kuwait", "restrictions": [4]},
    "LB": {"name": "Lebanon", "restrictions": [3, 4]},
    "LY": {"name": "Libya", "restrictions": [3, 4]},
    "NI": {"name": "Nicaragua", "restrictions": [3]},
    "OM": {"name": "Oman", "restrictions": [4]},
    "PK": {"name": "Pakistan", "restrictions": [4]},
    "QA": {"name": "Qatar", "restrictions": [4]},
    "SA": {"name": "Saudi Arabia", "restrictions": [4]},
    "SO": {"name": "Somalia", "restrictions": [3]},
    "SS": {"name": "South Sudan (Republic of)", "restrictions": [3]},
    "SU": {"name": "Sudan", "restrictions": [3]},
    "SY": {"name": "Syria", "restrictions": [2, 3, 4]},
    "TW": {"name": "Taiwan**", "restrictions": [1]},
    "AE": {"name": "United Arab Emirates", "restrictions": [4]},
    "VE": {"name": "Venezuela", "restrictions": [3, 4]},
    "YE": {"name": "Yemen", "restrictions": [4]},
    "EH": {"name": "Western Sahara", "restrictions": [1]},
    "ZW": {"name": "Zimbabwe", "restrictions": [3]},
}


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
        lab_questions = {
            z["name"]: z["question"] for z in lab_obj.access_request_questions()
        }
        access_request_questions[request["labname"]] = lab_questions
        request["lab_friendly_name"] = lab_obj.get_lab_config().friendly_name

    return access_requests, access_request_questions


def get_country_list() -> dict:
    util_path = Path(__file__).parent.resolve().absolute()
    with open(util_path / "../data/countries.json", "r", encoding="utf-8") as f:
        return json.loads(f.read())


def restricted_countries_html_color(restrictions: list) -> str:
    if 4 in restrictions and 1 in restrictions:
        return "#F73B3B"  # Very Red
    if 4 in restrictions or 1 in restrictions:
        return "#F76060"  # Red
    if 2 in restrictions and 3 in restrictions:
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
