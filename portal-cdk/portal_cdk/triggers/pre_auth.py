# https://pypi.org/project/username-validator/
from username_validator import UsernameValidator

MY_RESERVED = ["opensciencelab", "opensarlab"]


def lambda_handler(event, context):
    validator = UsernameValidator(additional_names=MY_RESERVED)

    user = event["userName"]

    if not user.islower():
        raise Exception("Username must be lowercase")

    validator.validate_all(user)

    return event
