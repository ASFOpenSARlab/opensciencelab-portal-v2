import json
import os
import datetime

from util.responses import wrap_response
from util.exceptions import BadSsoToken
from util.session import current_session, PortalAuth
from util.user import User

import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from opensarlab.auth import encryptedjwt
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

logger = Logger(child=True)

PORTAL_USER_COOKIE = "portal-username"
COGNITO_JWT_COOKIE = "portal-jwt"

# FIXME: These values should all be passed in dynamically!
AWS_DEFAULT_REGION = os.getenv("STACK_REGION")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_POOL_ID = os.getenv("COGNITO_POOL_ID")
COGNITO_PUBLIC_KEYS_URL = (
    f"https://cognito-idp.{AWS_DEFAULT_REGION}.amazonaws.com/"
    + COGNITO_POOL_ID
    + "/.well-known/jwks.json"
)
COGNITO_DOMAIN_ID = os.getenv("COGNITO_DOMAIN_ID")
COGNITO_HOST = (
    f"https://{COGNITO_DOMAIN_ID}.auth.{AWS_DEFAULT_REGION}.amazoncognito.com"
)

CLOUDFRONT_ENDPOINT = os.getenv("CLOUDFRONT_ENDPOINT")
LOGIN_URL = (
    COGNITO_HOST
    + "/login?"
    + f"client_id={COGNITO_CLIENT_ID}&"
    + "response_type=code&"
    + "scope=aws.cognito.signin.user.admin+email+openid+phone+profile&"
    + f"redirect_uri=https://{CLOUDFRONT_ENDPOINT}/auth"
)

LOGOUT_URL = (
    COGNITO_HOST
    + "/logout?"
    + f"client_id={COGNITO_CLIENT_ID}&"
    + f"logout_uri=https://{CLOUDFRONT_ENDPOINT}/logout"
)

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


def get_key_validation():
    global JWT_VALIDATION

    if not JWT_VALIDATION:
        public_keys = {}
        logger.debug({"keys": COGNITO_PUBLIC_KEYS_URL})
        jwks = requests.get(COGNITO_PUBLIC_KEYS_URL).json()
        for jwk in jwks["keys"]:
            kid = jwk["kid"]
            public_keys[kid] = RSAAlgorithm.from_jwk(json.dumps(jwk))

        JWT_VALIDATION = public_keys

    return JWT_VALIDATION


def get_param_from_jwt(jwt_cookie, param_name="username"):
    decoded = jwt.decode(jwt_cookie, options={"verify_signature": False})
    return decoded[param_name]


def validate_jwt(jwt_cookie):
    jwt_validation = get_key_validation()

    try:
        kid = jwt.get_unverified_header(jwt_cookie)["kid"]
        key = jwt_validation[kid]
        return jwt.decode(jwt_cookie, key, algorithms=["RS256"])
    except jwt.exceptions.ExpiredSignatureError:
        username = get_param_from_jwt(jwt_cookie, "username")
        logger.warning(f"Expired Token for user '{username}'")
    except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        logger.warning("Invalid JWT Token")

    return False


def validate_code(code, request_host):
    oauth2_token_url = f"{COGNITO_HOST}/oauth2/token"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": COGNITO_CLIENT_ID,
        "redirect_uri": f"https://{request_host}/auth",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    logger.debug(
        {
            "exchange-data": data,
            "auth-host": oauth2_token_url,
        }
    )

    # Attempt to exchange a code for a Token
    token_data = requests.post(oauth2_token_url, data=data, headers=headers).json()

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


def get_set_cookie_headers(token):
    access_token_jwt = token["access_token"]
    id_token_jwt = token["id_token"]

    logger.debug({"access_token": access_token_jwt})
    logger.debug({"id_token": id_token_jwt})

    access_token_decoded = validate_jwt(access_token_jwt)

    ### id_token can be decoded with "aud":COGNITO_CLIENT_ID
    # id_token_decoded = validate_jwt(id_token_jwt)

    # make sure the JWT validated
    if not access_token_decoded:
        return []

    cookie_headers = []

    # Grab the username from access_token JWT, and encode it
    username = access_token_decoded.get("username", "Unknown")
    username_cookie_value = encrypt_data(username)

    # Format "Set-Cookie" headers
    cookie_headers.append(f"{PORTAL_USER_COOKIE}={username_cookie_value};")
    cookie_headers.append(f"{COGNITO_JWT_COOKIE}={access_token_jwt};")

    logger.debug({"set-cookie-headers": cookie_headers})

    return cookie_headers


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
    past_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
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
        jwt_cookie = cookies.get(COGNITO_JWT_COOKIE)
        current_session.auth.cognito.raw = jwt_cookie

        validated_jwt = validate_jwt(jwt_cookie)
        logger.debug({"jwt_cookie_payload": validated_jwt})

        if validated_jwt:
            jwt_username = validated_jwt["username"]
            logger.debug("JWT Username is %s", jwt_username)
            current_session.auth.cognito.decoded = validated_jwt
            current_session.auth.cognito.username = jwt_username
            current_session.auth.cognito.valid = True

            # Get User info
            current_session.user = User(username=jwt_username)

    else:
        logger.debug(f"No {COGNITO_JWT_COOKIE} cookie provided")

    # process the actual request
    return handler(event, context)


def require_auth(roles: list=["user"]):
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
            
            session_roles = current_session.user.roles
            logger.info(f"User '{username}' has {session_roles} roles, requires {roles}")
            if session_roles not in roles:
                logger.info("User is not authorized")
                #return wrap_response(
                #    body="User is not authorized",
                #    code=401,
                #    cookies=cookies,
                #)

            # Run the endpoint
            return func(*args, **kwargs)

        return wrapper

    return inner
