
from util.exceptions import DbError

def validate(key, value):
    try:
        return validator_map[key](value)
    except ValueError as e:
        raise DbError(f"Invalid value for {key}: {value}. Error: {e}") from e

validator_map = {
    "access": list,
    "some_int_without_default": int,
    "some_int_with_default": int,
}
