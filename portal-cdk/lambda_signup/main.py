import re

## Keep both these here, so the test suite can use them too:
#   The 'r' string is to not escape the backslashes
USERNAME_REGEX = r"^[a-zA-Z0-9\._-]+$"
#   The '- ' to separate this from the previous message in the cognito login UI.
#     (And the message already ends in a period.)
ERROR_MESSAGE = (
    "- Username contains invalid special characters. "
    "Only periods, underscores, and dashes allowed"
)

def lambda_handler(event, _context):
    if re.match(USERNAME_REGEX, event["userName"]) is None:
        raise ValueError(ERROR_MESSAGE)
    # Return to Amazon Cognito
    return event
