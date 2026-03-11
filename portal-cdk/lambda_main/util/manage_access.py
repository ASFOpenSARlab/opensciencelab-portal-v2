from objs.user import User
from util.labs import LAB_CONFIGS


def validate_edit_user_request(body: dict) -> tuple[bool, str]:
    # check always required keys are provided
    keys = ["username", "action"]
    for key in keys:
        if key not in body:
            return False, f"{key} not provided to edit_user"

    if body["action"] == "add_user":
        # check adding user fields provided
        keys = ["lab_profiles", "time_quota", "lab_country_status"]
        for key in keys:
            if key not in body:
                return False, f"{key} not provided to edit_user"
        return True, "Ready to add user"

    elif body["action"] == "remove_user":
        # check removing user fields provided
        return True, "Ready to remove user"

    else:
        return False, "Invalid action"


def validate_delete_lab_access(
    delete_lab_request: dict, user: User
) -> tuple[bool, str]:
    # Validate input is correct type
    if not isinstance(delete_lab_request, dict):
        return False, "Body is not correct type"

    # Validate input has key "labs"
    if "labs" not in delete_lab_request:
        return False, "Does not contain 'labs' key"

    for lab_name, lab_data in delete_lab_request["labs"].items():
        # Ensure lab exist
        if lab_name not in LAB_CONFIGS:
            return False, f"Lab does not exist: {lab_name}"

        if not isinstance(lab_data, dict):
            return False, f"Lab data for {lab_name} is not a dict"
    ## Get all the keys from delete_lab_request, that are NOT in user labs:
    # (Need to do this last, since lab A might fail linting above
    #  and you'd want error that first)
    already_removed_labs = [
        key for key in delete_lab_request["labs"] if key not in user.labs
    ]
    if already_removed_labs:
        # Still return 200, but change the message:
        return (
            True,
            f"User isn't already apart of labs: {', '.join(already_removed_labs)}",
        )
    return True, "Success"


def validate_set_lab_access(put_lab_request: dict) -> tuple[bool, str]:
    # Validate input is correct type
    if not isinstance(put_lab_request, dict):
        return False, "Body is not correct type"

    # Validate input has key "labs"
    if "labs" not in put_lab_request:
        return False, "Does not contain 'labs' key"

    for lab_name in put_lab_request["labs"].keys():
        # Ensure lab exist
        if lab_name not in LAB_CONFIGS:
            return False, f"Lab does not exist: {lab_name}"

        # Check all lab fields exist and are correct type
        all_fields = {
            "lab_profiles": list,
            "time_quota": str,
            "lab_country_status": str,
        }
        for field, _ in all_fields.items():
            if put_lab_request["labs"][lab_name].get(field) is None:
                return False, f"Field '{field}' not provided for lab {lab_name}"

            if not isinstance(
                put_lab_request["labs"][lab_name][field], all_fields[field]
            ):
                return False, f"Field '{field}' not of type {all_fields[field]}"

        # Ensure all profiles exist for a given lab
        for profile in put_lab_request["labs"][lab_name]["lab_profiles"]:
            # If the lab doesn't have the profile you're trying to set:
            if profile not in LAB_CONFIGS[lab_name].allowed_profiles:
                return False, f"Profile '{profile}' not allowed for lab {lab_name}"

    return True, "Success"


def validate_edit_tokens_request(body: dict) -> tuple[bool, str]:
    # check always required keys are provided
    keys = ["action"]
    for key in keys:
        if key not in body:
            return False, f"{key} not provided to edit_tokens"

    if body["action"] == "add_token":
        # check adding token fields provided
        keys = ["lab_profiles"]
        for key in keys:
            if key not in body:
                return False, f"{key} not provided to edit_tokens"
        return True, "Ready to add token"

    elif body["action"] == "remove_token":
        keys = ["token"]
        for key in keys:
            if key not in body:
                return False, f"{key} not provided to edit_tokens"
        # check removing token fields provided
        return True, "Ready to remove token"

    else:
        return False, "Invalid action"
