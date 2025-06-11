"""A list of attributes, and what to validate them with."""

from util.exceptions import DbError

from .validators import (
    dict_contains_random_key,
    validate_profile,
)


def validate(key, value):
    try:
        return validator_map[key](value)
    except ValueError as e:
        raise DbError(f"Invalid value for {key}: {value}. Error: {e}") from e


validator_map = {
    "access": list,
    "some_int_without_default": int,
    "some_int_with_default": int,
    "random_dict": dict_contains_random_key,
    "profile": validate_profile,
    "last_cookie_assignment": str,
    "require_profile_update": bool,
}
