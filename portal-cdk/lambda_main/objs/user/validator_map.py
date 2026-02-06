"""A list of attributes, and what to validate them with."""

from .validators import validate_profile

validator_map = {
    "access": list,
    "profile": validate_profile,
    "last_cookie_assignment": str,
    "require_profile_update": bool,
    "labs": dict,
    "email": str,
    "_rec_counter": int,
    "ip_address": str,
    "country_code": str,
}
