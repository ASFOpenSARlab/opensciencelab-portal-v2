"""A list of attributes, and what to validate them with."""

from util.exceptions import DbError


def validate(key, value):
    try:
        return validator_map[key](value)
    except ValueError as e:
        raise DbError(f"Invalid value for {key}: {value}. Error: {e}") from e


validator_map = {
    "access_requests": list,
    "access_tokens": list,
    "_rec_counter": int,
}
