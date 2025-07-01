import os
import boto3

AWS_DEFAULT_REGION = os.getenv("STACK_REGION", "us-west-2")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_DOMAIN_ID = os.getenv("COGNITO_DOMAIN_ID")
COGNITO_HOST = (
    f"https://{COGNITO_DOMAIN_ID}.auth.{AWS_DEFAULT_REGION}.amazoncognito.com"
)
COGNITO_POOL_ID = os.getenv("COGNITO_POOL_ID")
COGNITO_PUBLIC_KEYS_URL = (
    f"https://cognito-idp.{AWS_DEFAULT_REGION}.amazonaws.com/"
    + COGNITO_POOL_ID
    + "/.well-known/jwks.json"
)

_COGNITO_CLIENT = boto3.client("cognito-idp", region_name=AWS_DEFAULT_REGION)


def get_user_from_user_pool(username) -> dict:
    try:
        return _COGNITO_CLIENT.admin_get_user(
            UserPoolId=COGNITO_POOL_ID, Username=username
        )
    except _COGNITO_CLIENT.exceptions.UserNotFoundException:
        # User does not exist
        pass

    return {}


def delete_user_from_user_pool(username) -> bool:
    # trigger user delete
    try:
        _COGNITO_CLIENT.admin_delete_user(UserPoolId=COGNITO_POOL_ID, Username=username)
    except _COGNITO_CLIENT.exceptions.UserNotFoundException:
        # Could not find the user to delete it
        return False

    if get_user_from_user_pool(username).get("Username"):
        # If we get a response, the user was NOT delete.
        return False
    return True
