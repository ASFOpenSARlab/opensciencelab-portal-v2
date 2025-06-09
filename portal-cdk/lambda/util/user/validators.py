"""A list of validators, for custom parsing input data."""


def dict_contains_random_key(validate_dict):
    validate_dict = dict(validate_dict)
    if "random" not in validate_dict:
        raise ValueError("Missing 'random' key in dictionary.")
    return validate_dict


def validate_profile(validate_dict):
    validate_dict = dict(validate_dict)
    expected_keys = [
        "country_of_residence",
        "is_affiliated_with_nasa",
        "user_or_pi_nasa_email",
        "user_affliated_with_nasa_research_email",
        "pi_affliated_with_nasa_research_email",
        "is_affiliated_with_us_gov_research",
        "user_affliated_with_gov_research_email",
        "is_affliated_with_isro_research",
        "user_affliated_with_isro_research_email",
        "is_affliated_with_university",
        "faculty_member_affliated_with_university",
        "research_member_affliated_with_university",
        "graduate_student_affliated_with_university",
    ]

    # Check if each key is missing
    missing_keys = []
    for key in expected_keys:
        if key not in validate_dict:
            missing_keys.append(key)

    # Throw error with list of missing keys if some keys are missing
    if missing_keys:
        missing_keys_string = ", ".join(missing_keys)
        raise ValueError(
            f"Missing the following keys in dictionary: {missing_keys_string}"
        )

    return validate_dict
