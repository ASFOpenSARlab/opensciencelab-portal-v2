import os
from datetime import datetime, timedelta
import pytz
import boto3
from aws_lambda_powertools import Logger
import time


logger = Logger(child=True)

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

COGNITO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
MFA_RESET_WINDOW_MINUTES = 10


def get_user_from_user_pool(username) -> dict:
    try:
        start_time = time.perf_counter()
        user = _COGNITO_CLIENT.admin_get_user(
            UserPoolId=COGNITO_POOL_ID, Username=username
        )
        logger.info(f"Fetching Cognito user took {time.time() - start_time} seconds")

        return user
    except _COGNITO_CLIENT.exceptions.UserNotFoundException:
        logger.warning(f"User {username} does not exist")
        pass

    return {}


def delete_user_from_user_pool(username) -> bool:
    # trigger user delete
    try:
        start_time = time.perf_counter()
        _COGNITO_CLIENT.admin_delete_user(UserPoolId=COGNITO_POOL_ID, Username=username)
        logger.info(f"Deleting Cognito user took {time.time() - start_time} seconds")
    except _COGNITO_CLIENT.exceptions.UserNotFoundException:
        # Could not find the user to delete it
        logger.error(f"User {username} could not be deleted")
        return False

    if get_user_from_user_pool(username).get("Username"):
        # If we get a response, the user was NOT delete.
        return False
    return True


def verify_user_password(username, password) -> bool:
    # Verify cognito user & password without MFA
    try:
        start_time = time.perf_counter()
        response = _COGNITO_CLIENT.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
            },
            ClientId=COGNITO_CLIENT_ID,
        )
        logger.info(
            f"Verifying Cognito user password took {time.time() - start_time} seconds"
        )
    except (
        _COGNITO_CLIENT.exceptions.UserNotFoundException,
        _COGNITO_CLIENT.exceptions.NotAuthorizedException,
    ) as e:
        # Could not verify user
        logger.warning(f"Could not verify password for user {username}: {e}.")
        return False

    if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        # Username & Password match in cognito
        return True

    # Unknown other scenario
    logger.error(f"Received unexpect response from initiate_auth(): {response}")
    return False


def recreate_cognito_user(user, suppress_email=True) -> bool:
    start_time = time.perf_counter()
    response = _COGNITO_CLIENT.admin_create_user(
        UserPoolId=COGNITO_POOL_ID,
        Username=user["Username"],
        MessageAction="SUPPRESS" if suppress_email else "RESEND",
        UserAttributes=[
            attr for attr in user["UserAttributes"] if attr["Name"] != "sub"
        ],
    ).get("User")
    logger.info(f"Creating Cognito user took {time.time() - start_time} seconds")

    if response.get("Username") == user["Username"]:
        return True

    # Could not recreate user?
    logger.error(f"Could not recreate User {user['Username']}: {response}.")
    return False


def set_cognito_user_password(username, password) -> bool:
    try:
        start_time = time.perf_counter()
        _COGNITO_CLIENT.admin_set_user_password(
            UserPoolId=COGNITO_POOL_ID,
            Username=username,
            Password=password,
            Permanent=True,
        )
        logger.info(
            f"Setting Cognito user password took {time.time() - start_time} seconds"
        )
    except Exception as E:
        logger.error(f"Could not set password for User {username}: {E}")
        return False

    return True


def reset_user_mfa(username, password=None) -> bool:
    existing_user = get_user_from_user_pool(username)
    if not existing_user.get("Username"):
        return False

    logger.info(f"Deleting {username} from userpool")
    if not delete_user_from_user_pool(username):
        return False

    logger.info(f"Recreating {username}")
    if not recreate_cognito_user(existing_user):
        return False

    if password:
        logger.info(f"Setting password for {username}")
        if not set_cognito_user_password(username, password):
            return False

    return True


def set_cognito_user_attribute(username, attribute_name, attribute_value=None) -> bool:
    try:
        if attribute_value:
            if isinstance(attribute_value, datetime):
                attribute_value = attribute_value.strftime(COGNITO_DATETIME_FORMAT)
            start_time = time.perf_counter()
            _COGNITO_CLIENT.admin_update_user_attributes(
                UserPoolId=COGNITO_POOL_ID,
                Username=username,
                UserAttributes=[
                    {"Name": "custom:" + attribute_name, "Value": attribute_value},
                ],
            )
            logger.info(
                f"Setting Cognito user custom attribute took {time.time() - start_time} seconds"
            )
        else:
            start_time = time.perf_counter()
            _COGNITO_CLIENT.admin_delete_user_attributes(
                UserPoolId=COGNITO_POOL_ID,
                Username=username,
                UserAttributeNames=["custom:" + attribute_name],
            )
            logger.info(
                f"Deleting Cognito user custom attribute took {time.time() - start_time} seconds"
            )

    except _COGNITO_CLIENT.exceptions.UserNotFoundException:
        return False

    except Exception as E:
        logger.error(
            f"Problem updating Attr {attribute_name} to {attribute_value}: {E}"
        )
        return False

    return True


def get_cognito_user_attribute(username, attribute_name) -> bool | None | datetime:
    existing_user = get_user_from_user_pool(username)
    if not existing_user.get("Username"):
        return False

    # Non-custom attributes
    if attribute_name not in ("email"):
        attribute_name = "custom:" + attribute_name

    for attribute in existing_user.get("UserAttributes", []):
        if attribute["Name"] == attribute_name:
            if attribute_name.endswith("mfa_reset_date"):
                return pytz.utc.localize(
                    datetime.strptime(attribute["Value"], COGNITO_DATETIME_FORMAT)
                )
            return attribute["Value"]

    logger.warning(f"Attribute {attribute_name} not found in {existing_user}")

    return None


def check_mfa_reset_window(username) -> bool:
    reset_time = get_cognito_user_attribute(username, "mfa_reset_date")
    return reset_time >= datetime.now(pytz.UTC) - timedelta(
        minutes=MFA_RESET_WINDOW_MINUTES
    )


def set_mfa_reset_values(username, reset_code):
    current_time = datetime.now(pytz.UTC).replace(microsecond=0)
    set_cognito_user_attribute(username, "mfa_reset_date", current_time)
    set_cognito_user_attribute(username, "mfa_reset_code", reset_code)


def reset_user_mfa_with_password(username, password, reset_code) -> bool:
    # Make sure password validates
    if not verify_user_password(username, password):
        logger.warning(f"Could not verify user {username} for MFA reset")
        return False

    # Make sure we're in the window
    if not check_mfa_reset_window(username):
        logger.warning("MFA Reset not in acceptable window")
        return False

    if not get_cognito_user_attribute(username, "mfa_reset_code") == reset_code:
        logger.warning("MFA Reset code is not valid")
        return False

    # All params passed, removed reset info before copy
    set_cognito_user_attribute(username, "mfa_reset_code")
    set_cognito_user_attribute(username, "mfa_reset_date")

    return reset_user_mfa(username, password)


def all_locked_users() -> set[str]:
    # Get all disabled users
    start_time = time.perf_counter()
    all_disabled_res = _COGNITO_CLIENT.list_users(
        UserPoolId=os.environ.get("USER_POOL_ID"), Filter='status = "false"'
    )
    logger.info(
        f"Getting list of locked Cognito users took {time.time() - start_time} seconds"
    )

    locked_users = set([r["Username"] for r in all_disabled_res["Users"]])

    if len(locked_users) > 50:
        logger.warning(
            "Too many locked users, either increase Limit in list_users call, add pagination, or delete locked users"
        )

    return locked_users


def disable_user(username):
    # trigger disable user
    try:
        start_time = time.perf_counter()
        _COGNITO_CLIENT.admin_disable_user(
            UserPoolId=COGNITO_POOL_ID, Username=username
        )
        logger.info(f"Locking Cognito user took {time.time() - start_time} seconds")
    except _COGNITO_CLIENT.exceptions.UserNotFoundException:
        # Could not find the user to delete it
        return False
    except Exception as e:
        logger.warning(f"ERROR Disabling user: {e}")


def enable_user(username):
    # trigger enable user
    try:
        start_time = time.perf_counter()
        _COGNITO_CLIENT.admin_enable_user(UserPoolId=COGNITO_POOL_ID, Username=username)
        logger.info(f"Unlocking Cognito user took {time.time() - start_time} seconds")
    except _COGNITO_CLIENT.exceptions.UserNotFoundException:
        # Could not find the user to delete it
        return False
    except Exception as e:
        logger.warning(f"ERROR Enabling user: {e}")
