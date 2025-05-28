"""A list of validators, for custom parsing input data."""


def dict_contains_random_key(validate_dict):
    validate_dict = dict(validate_dict)
    if "random" not in validate_dict:
        raise ValueError("Missing 'random' key in dictionary.")
    return validate_dict
