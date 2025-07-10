import json
import os
import datetime
from cachetools import TTLCache

from util.user import User
from util.responses import wrap_response
from util.exceptions import BadSsoToken, UnknownUser
from util.session import current_session, PortalAuth
from util.format import render_template
import util.cognito

import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from opensarlab.auth import encryptedjwt
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

logger = Logger(child=True)

# Refresh token cache, upto 100 items, max life 10mins
REFRESH_CACHE = TTLCache(maxsize=100, ttl=10 * 60)

PORTAL_USER_COOKIE = "portal-username"
COGNITO_JWT_COOKIE = "portal-jwt"

TOKEN_URL = f"{util.cognito.COGNITO_HOST}/oauth2/token"

REVOKE_TOKEN_URL = f"{util.cognito.COGNITO_HOST}/oauth2/revoke"

SSO_TOKEN_SECRET_NAME = os.getenv("SSO_TOKEN_SECRET_NAME")

JWT_VALIDATION = None
USER_PROFILES = {}


def encrypt_data(data: dict | str) -> str:
    sso_token = parameters.get_secret(SSO_TOKEN_SECRET_NAME)
    try:
        return encryptedjwt.encrypt(data, sso_token=sso_token)
    except encryptedjwt.BadTokenException as e:
        msg = "\n".join(
            [
                "Deploy Error, make sure to change the SSO Secret.",
                "(In Secrets: retrieve the value, then the edit button will appear).",
            ]
        )
        raise BadSsoToken(msg, error_code=401) from e


def decrypt_data(data):
    sso_token = parameters.get_secret(SSO_TOKEN_SECRET_NAME)
    return encryptedjwt.decrypt(data, sso_token=sso_token)


def refresh_map_del(refresh_token) -> bool:
    # Delete an item from refesh cache
    if refresh_token in REFRESH_CACHE:
        del REFRESH_CACHE[refresh_token]
    return True


def refresh_map(refresh_token):
    if refresh_token in REFRESH_CACHE:
        tokens = REFRESH_CACHE[refresh_token]
        access_token = tokens["access_token"]
        if validate_jwt(access_token):
            logger.info("Access token found in refresh map")
            return tokens

    tokens = get_tokens_from_refresh(refresh_token)
    if not tokens.get("access_token"):
        logger.warning("Refresh token exchange failed")
        return {}

    access_token = tokens.get("access_token")

    if validate_jwt(access_token):
        # Save new access token to cache
        REFRESH_CACHE[refresh_token] = tokens
        return tokens

    logger.warning("Refresh token missing or invalid")
    return {}


def get_key_validation():
    global JWT_VALIDATION

    if not JWT_VALIDATION:
        public_keys = {}
        logger.debug({"keys": util.cognito.COGNITO_PUBLIC_KEYS_URL})
        jwks = requests.get(util.cognito.COGNITO_PUBLIC_KEYS_URL).json()
        for jwk in jwks["keys"]:
            kid = jwk["kid"]
            public_keys[kid] = RSAAlgorithm.from_jwk(json.dumps(jwk))

        JWT_VALIDATION = public_keys

    return JWT_VALIDATION


def get_param_from_jwt(jwt_cookie, param_name="username"):
    decoded = jwt.decode(jwt_cookie, options={"verify_signature": False})
    return decoded[param_name]


def validate_jwt(jwt_cookie, aud=None):
    if not jwt_cookie:
        return False

    jwt_validation = get_key_validation()

    try:
        kid = jwt.get_unverified_header(jwt_cookie)["kid"]
        key = jwt_validation[kid]
        return jwt.decode(jwt_cookie, key, audience=aud, algorithms=["RS256"])
    except jwt.exceptions.ExpiredSignatureError:
        username = get_param_from_jwt(jwt_cookie, "username")
        logger.warning(f"Expired Token for user '{username}'")
    except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        logger.warning("Invalid JWT Token")

    return False


def get_token_data_and_headers():
    data = {"client_id": util.cognito.COGNITO_CLIENT_ID}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    return data, headers


def revoke_refresh_token(refresh_token):
    data, headers = get_token_data_and_headers()
    data["token"] = refresh_token
    response = requests.post(REVOKE_TOKEN_URL, data=data, headers=headers).content
    logger.info("Revoke token response: %s", response)


def get_tokens_from_refresh(refresh_token):
    data, headers = get_token_data_and_headers()
    data["grant_type"] = "refresh_token"
    data["refresh_token"] = refresh_token

    logger.debug("Refresh Token exchange @ %s w/ %s", TOKEN_URL, data)

    # Attempt to exchange a code for a Token
    token_data = requests.post(TOKEN_URL, data=data, headers=headers).json()
    logger.debug("post response token_data: %s", token_data)
    if token_data.get("access_token"):
        logger.debug("Successfully converted refresh to access token")
        return token_data

    logger.warning("Refresh token exchange failed: %s", token_data)
    return {}


def validate_code(code, request_host):
    data, headers = get_token_data_and_headers()

    # Non-generic params
    data["grant_type"] = "authorization_code"
    data["code"] = code
    data["redirect_uri"] = f"https://{request_host}/auth"

    logger.debug(
        {
            "exchange-data": data,
            "auth-host": TOKEN_URL,
        }
    )

    # Attempt to exchange a code for a Token
    token_data = requests.post(TOKEN_URL, data=data, headers=headers).json()

    if token_data.get("id_token"):
        return token_data
    else:
        logger.error(
            {
                "token-exchange-error": token_data,
                "code": code,
            }
        )
        return False


def get_set_cookie_header(name, value):
    return {"Set-Cookie": f"{name}={value}"}


def get_jwt_from_token(token, token_name):
    return token[token_name]


def parse_token(token):
    access_token_jwt = token["access_token"]
    id_token_jwt = token["id_token"]
    refresh_token_jwt = token["refresh_token"]

    # Add tokens to TTL Cache
    REFRESH_CACHE[refresh_token_jwt] = token

    logger.debug({"refresh_token": refresh_token_jwt})
    logger.debug({"access_token": access_token_jwt})
    logger.debug({"id_token": id_token_jwt})

    access_token_decoded = validate_jwt(access_token_jwt)

    ### id_token can be decoded with "aud":COGNITO_CLIENT_ID
    # id_token_decoded = validate_jwt(id_token_jwt)

    cookie_headers = []

    # Grab the username from access_token JWT, and encode it
    username = access_token_decoded.get("username", "Unknown")
    if username == "Unknown":
        raise (UnknownUser("Unknown user from decoded access token"))

    username_cookie_value = encrypt_data(username)

    # Format "Set-Cookie" headers
    cookie_headers.append(f"{PORTAL_USER_COOKIE}={username_cookie_value};")
    cookie_headers.append(f"{COGNITO_JWT_COOKIE}={refresh_token_jwt};")

    logger.debug({"set-cookie-headers": cookie_headers})

    # Create and return parsed token
    token_dict = {
        "username": username,
        "cookie_headers": cookie_headers,
    }

    return token_dict


def get_encoded_username_cookie(username):
    # Return portal-compatible username cookie
    return {PORTAL_USER_COOKIE: decrypt_data(username)}


def get_cookies_from_event(event):
    cookies = {}
    if "cookies" not in event:
        return cookies
    for cookie in event["cookies"]:
        cookie_parts = cookie.split("=")
        cookies[cookie_parts[0]] = "=".join(cookie_parts[1:])
    return cookies


def delete_cookies():
    past_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
    expires_str = past_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
    cookies = []
    for cookie in [PORTAL_USER_COOKIE, COGNITO_JWT_COOKIE]:
        cookies.append(f"{cookie}=; Expires={expires_str};")

    return cookies


@lambda_handler_decorator
def process_auth(handler, event, context):
    # Cookies we care about:
    cookies = get_cookies_from_event(event)
    current_session.auth = PortalAuth()
    current_session.user = None

    if cookies.get(PORTAL_USER_COOKIE):
        portal_username_cookie = cookies.get(PORTAL_USER_COOKIE)
        current_session.auth.portal_username.raw = portal_username_cookie
    else:
        logger.debug(f"No {PORTAL_USER_COOKIE} cookie provided")

    if cookies.get(COGNITO_JWT_COOKIE):
        # jwt_cookie is the Cognito REFRESH token
        jwt_cookie = cookies.get(COGNITO_JWT_COOKIE)
        current_session.auth.cognito.raw = jwt_cookie

        # Attempt to convert REFRESH to ACCESS token
        tokens = refresh_map(jwt_cookie)
        access_token = tokens.get("access_token")
        validated_access_jwt = validate_jwt(access_token)
        validated_id_jwt = validate_jwt(
            tokens.get("id_token"),
            aud=util.cognito.COGNITO_CLIENT_ID,
        )
        logger.debug({"validated_access_jwt": validated_access_jwt})
        logger.debug({"validated_id_jwt": validated_id_jwt})

        if validated_access_jwt:
            jwt_username = validated_access_jwt["username"]
            logger.debug("JWT Username is %s", jwt_username)
            current_session.auth.cognito.decoded = validated_access_jwt
            current_session.auth.cognito.username = jwt_username
            current_session.auth.cognito.email = validated_id_jwt["email"]
            current_session.auth.cognito.valid = True

            # Get User info
            current_session.user = User(username=jwt_username)
            # Check that we have the correct email
            if current_session.user.email != validated_id_jwt["email"]:
                logger.debug(
                    "Setting user %s email to %s",
                    jwt_username,
                    validated_id_jwt["email"],
                )
                current_session.user.email = validated_id_jwt["email"]

    else:
        logger.debug(f"No {COGNITO_JWT_COOKIE} cookie provided")

    # process the actual request
    return handler(event, context)


def require_access(access="user"):
    def inner(func):
        def wrapper(*args, **kwargs):
            # app is pulled in from outer scope via a function attribute

            # Check for cookie auth
            username = current_session.auth.cognito.username

            if not username:
                return_path = (
                    current_session.app.current_event.request_context.http.path
                )

                # If a jwt cookie was provided, it must be bad, destroy it
                if current_session.auth.cognito.raw:
                    cookies = delete_cookies()
                    logger.info(f"Deleting bad cookies: {cookies=}")
                else:
                    cookies = []

                return wrap_response(
                    body="User is not logged in",
                    code=302,
                    headers={"Location": f"/?return={return_path}"},
                    cookies=cookies,
                )
            # Check if user is disabled:
            if current_session.user.is_locked:
                logger.warning("User %s is locked", username)
                return wrap_response(
                    body=render_template(
                        content=(
                            "Sorry, your account isn't available right now. "
                            f"Please reach out to {os.getenv('SES_EMAIL')} if you have any questions or concerns."
                        ),
                        title="OSL Portal - Account Locked"
                    ),
                    code=403,
                )
            # Ensure user has access they are trying to achieve
            if access not in current_session.user.access:
                logger.warning(
                    "User %s attempted to access %s which requires %s access (user has %s Privs)",
                    username,
                    current_session.app.current_event.request_context.http.path,
                    access,
                    ", ".join(current_session.user.access),
                )

                # Send the user back to home base
                return wrap_response(
                    body="User does not have required access",
                    code=302,
                    headers={"Location": "/portal"},
                )

            # Redirect if user flagged to fill profile
            requested_url = current_session.app.current_event.request_context.http.path
            profile_form_url = f"/portal/profile/form/{username}"
            if (
                current_session.user.require_profile_update
                and requested_url != profile_form_url
            ):
                requested_url = profile_form_url
                return wrap_response(
                    body="User must update profile",
                    code=302,
                    headers={"Location": requested_url},
                )
            logger.info("User %s has %s access", username, access)
            # Run the endpoint
            return func(*args, **kwargs)

        return wrapper

    return inner
