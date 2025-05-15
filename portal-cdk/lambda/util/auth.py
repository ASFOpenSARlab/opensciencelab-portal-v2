import json
import os
import traceback

from util.responses import wrap_response

import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from opensarlab.auth import encryptedjwt
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

logger = Logger(service="APP")

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
    return encryptedjwt.encrypt(data, sso_token=sso_token)


def decrypt_data(data):
    sso_token = parameters.get_secret(SSO_TOKEN_SECRET_NAME)
    return encryptedjwt.decrypt(data, sso_token=sso_token)


def get_user_from_event(app):
    raw_event = app.current_event.raw_event
    if "requestContext" in raw_event:
        if "cognito_username" in raw_event["requestContext"]:
            return raw_event["requestContext"]["cognito_username"]
    return None


def get_user_from_cookies(cookies):
    for cookie in cookies:
        if cookie.startswith(PORTAL_USER_COOKIE):
            # Decode the cookie value
            username = cookie.split("=")[1]
            return decrypt_data(username)
    return None


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
    alg = jwt.get_unverified_header(jwt_cookie)["alg"]
    kid = jwt.get_unverified_header(jwt_cookie)["kid"]
    key = jwt_validation[kid]

    try:
        return jwt.decode(jwt_cookie, key, algorithms=[alg])
    except jwt.exceptions.ExpiredSignatureError:
        username = get_param_from_jwt(jwt_cookie, "username")
        logger.warning(f"Expired Token for user '{username}'")

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


@lambda_handler_decorator
def process_auth(handler, event, context):
    try:
        print(json.dumps({"AuthEvent": event, "AuthContext": context}, default=str))
        # Cookies we care about:
        cookies = get_cookies_from_event(event)

        if cookies.get(PORTAL_USER_COOKIE):
            event["requestContext"]["portal_username_cookie"] = cookies.get(
                PORTAL_USER_COOKIE
            )

        if cookies.get(COGNITO_JWT_COOKIE):
            jwt_cookie = cookies.get(COGNITO_JWT_COOKIE)
            jwt_username = get_param_from_jwt(jwt_cookie, "username")
            event["requestContext"]["cognito_jwt_cookie"] = jwt_cookie
            event["requestContext"]["cognito_username"] = jwt_username
            logger.debug("JWT Username is %s", jwt_username)

            validated_jwt = validate_jwt(jwt_cookie)
            logger.debug({"jwt_cookie_payload": validated_jwt})
            if validated_jwt:
                event["requestContext"]["cognito_validated"] = validated_jwt

        # process the actual request
        return handler(event, context)
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        raise e


def require_access(access="user"):
    def inner(func):
        def wrapper(*args, **kwargs):
            # app is pulled in from outer scope via a function attribute
            app = require_access.router.app

            # Check for cookie auth
            username = get_user_from_event(app)

            if not username:
                return_path = app.current_event.request_context.http.path

                return wrap_response(
                    body="User is not logged in",
                    code=302,
                    headers={"Location": f"/?return={return_path}"},
                )

            logger.info("User %s has %s access", username, access)

            # Run the endpoint
            return func(*args, **kwargs)

        return wrapper

    return inner
