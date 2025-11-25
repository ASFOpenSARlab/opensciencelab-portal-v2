"""A list of attributes, and what to validate them with."""

from util.exceptions import DbError

from .validators import validate_profile


def validate(key, value):
    try:
        return validator_map[key](value)
    except ValueError as e:
        raise DbError(f"Invalid value for {key}: {value}. Error: {e}") from e


validator_map = {
    "access": list,
    "profile": validate_profile,
    "last_cookie_assignment": str,
    "require_profile_update": bool,
    "labs": dict,
    "email": str,
    "_rec_counter": int,
    "is_locked": bool,
    "ip_address": str,
    "country_code": str,
}
