import json
import os

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
COGNITO_CLIENT_ID = "7p0eqmc22apfu6inppmjhktb8r"
COGNITO_REDIRECT_URL = "https://dsgujfu16uv7m.cloudfront.net/portal"
COGNITO_PUBLIC_KEYS_URL = "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_JMoh1BWzT/.well-known/jwks.json"
COGNITO_HOST = "https://portalcdkstack-cs.auth.us-west-2.amazoncognito.com"

SSO_TOKEN_SECRET_NAME = os.getenv("SSO_TOKEN_SECRET_NAME")

JWT_VALIDATION = None
USER_PROFILES = {}

def encrypt_data(data: dict | str) -> str:
    sso_token = parameters.get_secret(SSO_TOKEN_SECRET_NAME)
    return encryptedjwt.encrypt(data, sso_token=sso_token)

def decrypt_data(data):
    sso_token = parameters.get_secret(SSO_TOKEN_SECRET_NAME)
    return encryptedjwt.decrypt(data, sso_token=sso_token)

def get_key_validation():
    global JWT_VALIDATION

    if not JWT_VALIDATION:
        public_keys = {}
        jwks = requests.get(COGNITO_PUBLIC_KEYS_URL).json()
        for jwk in jwks['keys']:
            kid = jwk['kid']
            public_keys[kid] = RSAAlgorithm.from_jwk(json.dumps(jwk))

        JWT_VALIDATION = public_keys

    return JWT_VALIDATION

def get_param_from_jwt(jwt_cookie, param_name="username"):
    decoded = jwt.decode(jwt_cookie, options={"verify_signature": False})
    return decoded[param_name]

def validate_jwt(jwt_cookie):
    jwt_validation = get_key_validation()
    alg = jwt.get_unverified_header(jwt_cookie)['alg']
    kid = jwt.get_unverified_header(jwt_cookie)['kid']
    key = jwt_validation[kid]

    try:
        return jwt.decode(jwt_cookie, key, algorithms=[alg])
    except jwt.exceptions.ExpiredSignatureError as expired:
        username = get_param_from_jwt(jwt_cookie, "username")
        logger.warning(f"Expired Token for user '{username}'")

    return False

def validate_code(code):

    oauth2_token_url = f"{COGNITO_HOST}/oauth2/token"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": COGNITO_CLIENT_ID,
        "redirect_uri": COGNITO_REDIRECT_URL,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

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
    access_token_jwt = token['access_token']
    id_token_jwt = token['id_token']

    logger.info({"access_token": access_token_jwt})
    logger.info({"id_token": id_token_jwt})

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

    logger.info({"set-cookie-headers": cookie_headers})

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

    # Cookies we care about:
    cookies = get_cookies_from_event(event)

    if cookies.get(PORTAL_USER_COOKIE):
        event["requestContext"]["portal-username-cookie"] = cookies.get(PORTAL_USER_COOKIE)

    if cookies.get(COGNITO_JWT_COOKIE):
        jwt_cookie = cookies.get(COGNITO_JWT_COOKIE)
        event["requestContext"]["cognito-jwt-cookie"] = jwt_cookie
        event["requestContext"]["cognito-username"] = get_param_from_jwt(jwt_cookie, "username")

        validated_jwt = validate_jwt(jwt_cookie)
        if validated_jwt:
            event["requestContext"]["cognito-validated"] = validated_jwt

    # process the actual request
    return handler(event, context)
