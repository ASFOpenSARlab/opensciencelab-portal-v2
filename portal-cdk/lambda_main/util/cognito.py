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

DEPLOYMENT_HOSTNAME = os.getenv("DEPLOYMENT_HOSTNAME")
LOGIN_URL = (
    COGNITO_HOST
    + "/login?"
    + f"client_id={COGNITO_CLIENT_ID}&"
    + "response_type=code&"
    + "scope=aws.cognito.signin.user.admin+email+openid+phone+profile&"
    + f"redirect_uri=https://{DEPLOYMENT_HOSTNAME}/auth"
)

FORGOT_PASSWORD_URL = (
    COGNITO_HOST
    + "/forgotPassword?"
    + f"client_id={COGNITO_CLIENT_ID}&"
    + "response_type=code&"
    + "scope=aws.cognito.signin.user.admin+email+openid+phone+profile&"
    + f"redirect_uri=https://{DEPLOYMENT_HOSTNAME}/auth"
)

SIGNUP_URL = (
    COGNITO_HOST
    + "/signup?"
    + f"client_id={COGNITO_CLIENT_ID}&"
    + "response_type=code&"
    + "scope=aws.cognito.signin.user.admin+email+openid+phone+profile&"
    + f"redirect_uri=https://{DEPLOYMENT_HOSTNAME}/auth"
)

LOGOUT_URL = (
    COGNITO_HOST
    + "/logout?"
    + f"client_id={COGNITO_CLIENT_ID}&"
    + f"logout_uri=https://{DEPLOYMENT_HOSTNAME}/logout"
)


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
