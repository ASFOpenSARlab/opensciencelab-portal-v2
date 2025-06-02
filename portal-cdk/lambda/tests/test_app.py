import copy
import json
from dataclasses import dataclass
import time

from moto import mock_aws
import boto3

import main
from util.auth import PORTAL_USER_COOKIE, COGNITO_JWT_COOKIE

import pytest
import jwt
from jwt.algorithms import RSAAlgorithm

import util.user


REGION = "us-west-2"

BASIC_REQUEST = {
    "rawPath": "/test",
    "requestContext": {
        "requestContext": {"requestId": "227b78aa-779d-47d4-a48e-ce62120393b8"},
        "http": {"method": "GET", "path": "/test"},
        "stage": "$default",
    },
    "queryStringParameters": {},
    "cookies": [],
}

BAD_JWT = (
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6ImJsYSJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiw"
    "ibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTc0Nzk1OTY4MiwiZXhwIjoxNzQ3OTY"
    "zMjgyLCJ1c2VybmFtZSI6ImJhZF91c2VyIn0.GzmJ_7GBSMSrbt_HwfDE3Rc8X7O_9oTviC1eHWiDrgc"
)

OLD_JWT = (
    "eyJraWQiOiJLQkVnNE85NlB5eW4yazdmY0tkbDVMZjlPWkJJVFN5S1RqR3BLUHR5bURVPSIsImFsZyI6"
    "IlJTMjU2In0.eyJzdWIiOiI3ODExYjM2MC0xMDAxLTcwYTgtMTMxMy03OTE4YmI3ZTRiMTEiLCJpc3Mi"
    "OiJodHRwczpcL1wvY29nbml0by1pZHAudXMtd2VzdC0yLmFtYXpvbmF3cy5jb21cL3VzLXdlc3QtMl9S"
    "eTRYRnpaSnEiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzNGxwaHQ5MGRhY2xuZHY0M3BhNm8xaWRx"
    "YyIsIm9yaWdpbl9qdGkiOiI1NzAzNzk4NS1kODUwLTQ1ZjUtOGYwOS1hODY2NTliMjljZmMiLCJldmVu"
    "dF9pZCI6ImMzOTllNzBmLWQzNjQtNGI5MC1iMWVkLTJiNzY2YmJlZmM5YSIsInRva2VuX3VzZSI6ImFj"
    "Y2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4gcGhvbmUgb3BlbmlkIHBy"
    "b2ZpbGUgZW1haWwiLCJhdXRoX3RpbWUiOjE3NDcwODk4NzcsImV4cCI6MTc0NzA5MzQ3NywiaWF0Ijox"
    "NzQ3MDg5ODc3LCJqdGkiOiI2MjFmYzg5Ni1lN2ViLTQ4MjctYjQ2OS04OTYxYzExOTU1ZjgiLCJ1c2Vy"
    "bmFtZSI6ImJ0YnVlY2hsZXIifQ.PyFIJqkNpji7sebZJ1_XS3oEltzMhywQgSTYZ8l3RLJ9UP6wP-Ki9"
    "MK3t5XMCnHDGkcks0XXyZawlS5WIjx8k8wl_PBpBcKGRNcLj_loxXcHqvPJnHHEf_nc4YqNfxJ1dnTbt"
    "W69N-cnhuVaJReUItj5RpojebUyyAyPuT2J9bVM9SsGHKeuk1GPWyR8Xnrsix0lbmELTmfeepIyVJ0zP"
    "aHEauHCmRvXLR7QPywwQGcqA87_h4mL5CVWqm4Bq1DjM1gRMrcqsiFwWRLbAhtbj7_jsfRYbhtDHDqSb"
    "buljLV1SI8g3wyODtUuaSsLRPvnkhxcFtzxe15mcSQCP0SPIA"
)

JWK = {
    "alg": "RS256",
    "e": "AQAB",
    "kid": "KBEg4O96Pyyn2k7fcKdl5Lf9OZBITSyKTjGpKPtymDU=",
    "kty": "RSA",
    "n": (
        "wsYFkKoas_bVKdx3EvOdyQRXu40uZTr6BG11yWkOsZU9rRRK95sLbVhMq7oapK9Og5i5"
        "IQHCNDh6jyfq92SB44BjkSB2Q4ZsEvOM974yi5vtb42RnCtYsQrhV3iYxc3XbiUrDGon"
        "jUBdyV3Qsa09LmdI-O_4jSa8jzOLS4dXHrL-DGMklEmbwLM71e_mIiR6O5gutkghC83Y"
        "IWxSXUo1joBVt7lkd0vB6UKdmc3JuvxH5vhbrXelz3F49Xe0oeaN3UrotVXl0vnXsvtg"
        "6ftEjtQMi9RQ8c2mk77sjz8mjEUUSmhB6HN6uUh3iBygi8eYbhEBVP6h9vxxg1MGxjiP"
        "7Q"
    ),
    "use": "sig",
}


def validate_jwt(*args, **vargs):
    return {
        "client_id": "2pjp68mov6sfhqda8pjphll8cq",
        "token_use": "access",
        "auth_time": time.time(),
        "exp": time.time() + 100,
        "iat": time.time() - 100,
        "username": "test_user",
    }


def get_event(path="/", method="GET", cookies=None, headers=None, qparams=None):
    # This rather than defaulting to polluted dicts
    cookies = {} if not cookies else cookies
    headers = {} if not headers else headers
    qparams = {} if not qparams else qparams
    ret_event = copy.deepcopy(BASIC_REQUEST)

    # Update request path/method
    ret_event["rawPath"] = path
    ret_event["requestContext"]["http"]["path"] = path
    ret_event["requestContext"]["http"]["method"] = method

    for name, value in cookies.items():
        ret_event["cookies"].append(f"{name}={value}")

    for key, value in qparams.items():
        ret_event["queryStringParameters"][key] = value

    return ret_event


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    json_response_payload = {}

    if kwargs["data"]["code"] == "good_code":
        json_response_payload = {
            "id_token": "valid_id_token",
            "access_token": "valid_access_token",
        }

    if args[0].endswith("/oauth2/token"):
        return MockResponse(json_response_payload, 200)

    return MockResponse(None, 404)


@dataclass
class LambdaContext:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = "arn:aws:lambda:eu-west-1:123456789012:function:test"
    aws_request_id: str = "da658bd3-2d6f-4e7b-8ec2-937234644fdc"


@pytest.fixture
def lambda_context() -> LambdaContext:
    return LambdaContext()


@pytest.fixture
def fake_auth(monkeypatch):
    # Bypass JWT
    monkeypatch.setattr("util.auth.validate_jwt", validate_jwt)
    monkeypatch.setattr("jwt.decode", validate_jwt)

    # Override signing key
    monkeypatch.setattr(
        "aws_lambda_powertools.utilities.parameters.get_secret",
        lambda a: "er9LnqEOiH+JLBsFCy0kVeba6ZSlG903cliU7VYKnM8=",
    )

    auth_cookies = {PORTAL_USER_COOKIE: "bla", COGNITO_JWT_COOKIE: "bla"}

    return auth_cookies


class TestPortalIntegrations:
    def test_landing_handler(self, lambda_context: LambdaContext):
        event = get_event()

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert "Welcome to OpenScienceLab" in ret["body"]
        assert "Log in" in ret["body"]
        assert "/login?client_id=fake-cognito-id&response_type=code" in ret["body"]

    def test_not_logged_in(self, lambda_context: LambdaContext):
        event = get_event(path="/portal")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["body"] == "User is not logged in"
        assert ret["headers"].get("Location").endswith("?return=/portal")
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_static_image_dne(self, lambda_context: LambdaContext):
        event = get_event(path="/static/img/dne.png")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 404

    def test_static_image_bad_type(self, lambda_context: LambdaContext):
        event = get_event(path="/static/foo/bar.zip")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 404

    def test_static_image(self, lambda_context: LambdaContext):
        event = get_event(path="/static/img/jh_logo.png")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "image/png"

        event = get_event(path="/static/js/require.js")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "text/javascript"

        event = get_event(path="/static/css/style.min.css")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "text/css"

    def test_auth_no_code(self, lambda_context: LambdaContext):
        event = get_event(path="/auth")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 401
        assert ret["body"].find("No return Code found.") != -1
        assert not ret["headers"].get("Location")
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_auth_bad_code(self, lambda_context: LambdaContext, monkeypatch):
        monkeypatch.setattr("requests.post", mocked_requests_post)
        event = get_event(path="/auth", qparams={"code": "bad_code"})
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 401
        assert ret["body"].find("Could not complete token exchange") != -1

    def test_auth_good_code(self, lambda_context: LambdaContext, monkeypatch):
        monkeypatch.setattr("requests.post", mocked_requests_post)
        monkeypatch.setattr("util.auth.validate_jwt", validate_jwt)
        monkeypatch.setattr(
            "aws_lambda_powertools.utilities.parameters.get_secret",
            lambda a: "er9LnqEOiH+JLBsFCy0kVeba6ZSlG903cliU7VYKnM8=",
        )

        event = get_event(
            path="/auth",
            qparams={
                "code": "good_code",
                "state": "/portal/profile",
            },
        )
        ret = main.lambda_handler(event, lambda_context)

        cookies = [cookie.split("=")[0] for cookie in ret["cookies"]]
        assert ret["statusCode"] == 302
        assert PORTAL_USER_COOKIE in cookies
        assert COGNITO_JWT_COOKIE in cookies
        assert ret["headers"].get("Location") == "/portal/profile"
        assert ret["body"].find("Redirecting to /portal/profile") != -1

    def test_bad_jwt(self, lambda_context: LambdaContext, monkeypatch):
        monkeypatch.setattr("util.auth.get_key_validation", lambda: {"bla": "bla"})
        event = get_event(path="/portal", cookies={"portal-jwt": BAD_JWT})
        with pytest.raises(jwt.exceptions.InvalidAlgorithmError) as excinfo:
            main.lambda_handler(event, lambda_context)
        assert str(excinfo.value) == "The specified alg value is not allowed"

    def test_old_jwt(self, lambda_context: LambdaContext, monkeypatch):
        jwk_string = RSAAlgorithm.from_jwk(json.dumps(JWK))

        monkeypatch.setattr(
            "util.auth.get_key_validation",
            lambda: {
                "KBEg4O96Pyyn2k7fcKdl5Lf9OZBITSyKTjGpKPtymDU=": jwk_string,
            },
        )
        event = get_event(path="/portal/profile/joe", cookies={"portal-jwt": OLD_JWT})
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["body"] == "User is not logged in"
        assert ret["headers"].get("Location").endswith("?return=/portal/profile/joe")
        # Make sure we're setting cookies to an empty value
        assert ret["cookies"][0].find("Expires") != -1

    def test_logged_in(self, lambda_context: LambdaContext, fake_auth):
        event = get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Welcome to OpenScienceLab") != -1
        assert ret["headers"].get("Location") is None
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_log_out(self, lambda_context: LambdaContext):
        event = get_event(path="/logout")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        # Make sure we've been logged out
        assert ret["body"].find("You have been logged out") != -1
        assert ret["body"].find('<span id="login_widget">') != -1
        # And cookies are being expired
        assert ret["cookies"][0].find("Expires") != -1
        assert ret["cookies"][1].find("Expires") != -1

        # login_widget

    def test_post_portal_hub_auth(self, lambda_context: LambdaContext, fake_auth):
        event = get_event(path="/portal/hub/auth", method="POST", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "application/json"
        json_payload = json.loads(ret["body"])
        assert json_payload.get("message") == "OK"
        assert json_payload.get("data")

    def test_get_portal_hub_auth(self, lambda_context: LambdaContext, fake_auth):
        event = get_event(path="/portal/hub/login", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "text/html"
        assert ret["body"].find("hello - Cookie Created") != -1
        cookies = [cookie.split("=")[0] for cookie in ret["cookies"]]
        assert PORTAL_USER_COOKIE in cookies

    def test_get_portal_hub_no_auth(self, lambda_context: LambdaContext):
        event = get_event(path="/portal/hub", cookies={"foo": "bar"})
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["body"] == "User is not logged in"
        assert ret["headers"].get("Location").endswith("?return=/portal/hub")
        assert ret["headers"].get("Content-Type") == "text/html"


class TestPortalAuth:
    def test_generic_error(self, lambda_context: LambdaContext, monkeypatch):
        # Create an invalid SSO token
        monkeypatch.setattr(
            "aws_lambda_powertools.utilities.parameters.get_secret",
            lambda a: "this-is-bad-sso-token",
        )

        from util.auth import encrypt_data
        from util.exceptions import BadSsoToken

        with pytest.raises(BadSsoToken) as excinfo:
            encrypt_data("blablabla")
        assert str(excinfo.value).find("change the SSO Secret") != -1

# @pytest.fixture()
# def mock_db():
#     from util.user.user import User
#     from util.user.dynamo_db import delete_item
#     from util.exceptions import DbError
#     ## These imports have to be the long forum, to let us modify the values here:
#     # https://stackoverflow.com/a/12496239/11650472
#     import util
#     util.user.dynamo_db._DYNAMO_CLIENT = boto3.client("dynamodb", region_name=REGION)
#     util.user.dynamo_db._DYNAMO_DB = boto3.resource("dynamodb", region_name=REGION)
#     user_table_name = "TestUserTable"
#     print(f"Creating DynamoDB table {user_table_name} for tests")
#     util.user.dynamo_db._DYNAMO_DB.create_table(
#         TableName = user_table_name,
#         BillingMode = "PAY_PER_REQUEST",
#         KeySchema = [{"AttributeName": "username", "KeyType": "HASH"}],
#         AttributeDefinitions = [{
#             "AttributeName": "username",
#             "AttributeType": "S"
#         }],
#     )
#     print("Waiting for table to be created...")
#     util.user.dynamo_db._DYNAMO_TABLE = util.user.dynamo_db._DYNAMO_DB.Table(user_table_name)
#     return (
#         util.user.dynamo_db._DYNAMO_CLIENT,
#         util.user.dynamo_db._DYNAMO_DB,
#         util.user.dynamo_db._DYNAMO_TABLE,
#     )

@mock_aws
class TestUserClass:

    def setup_class():
        ## This is here just to fix a weird import timing issue with importing utils directly
        from util.user import dynamo_db as _import_proxy
        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util
        util.user.dynamo_db._DYNAMO_CLIENT = boto3.client("dynamodb", region_name=REGION)
        util.user.dynamo_db._DYNAMO_DB = boto3.resource("dynamodb", region_name=REGION)

    def setup_method(self, method):
        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util
        user_table_name = "TestUserTable"
        util.user.dynamo_db._DYNAMO_DB.create_table(
            TableName = user_table_name,
            BillingMode = "PAY_PER_REQUEST",
            KeySchema = [{"AttributeName": "username", "KeyType": "HASH"}],
            AttributeDefinitions = [{
                "AttributeName": "username",
                "AttributeType": "S"
            }],
        )
        util.user.dynamo_db._DYNAMO_TABLE = util.user.dynamo_db._DYNAMO_DB.Table(user_table_name)


    def test_username(self, lambda_context: LambdaContext):
        from util.user.user import User
        from util.exceptions import DbError
        import util
        # Username attr exists:
        username = "test_user"
        user = User(username)
        assert user.username == "test_user"

        # And you can't change it:
        with pytest.raises(DbError) as excinfo:
            user.username = "new_name"
        assert f"Key 'username' not in validator_map for user {user.username}" in str(excinfo.value)

    def test_is_default(self, lambda_context: LambdaContext):
        # Test this early, so we can use it in future tests
        from util.user.user import User

        username = "test_user"
        user = User(username)
        assert user.is_default("access", None) is False, "Access is not None"
        assert user.is_default("access", []) is False, "Access is not empty list"
        assert user.is_default("access", ["user"]) is True, "Access defaults to just 'user'"

    def test_defaults_applied(self, lambda_context: LambdaContext):
        from util.user.user import User
        from util.user.validator_map import validator_map
        from util.user.defaults import defaults
        from frozendict import deepfreeze

        username = "test_user"
        user = User(username)

        for attr in validator_map:
            if attr in defaults:
                # Deepfreeze modifies the value, so we need to compare it:
                assert getattr(user, attr) == deepfreeze(defaults[attr]), f"Default for '{attr}' should be applied"
            else:
                assert getattr(user, attr) is None, f"User should have attribute '{attr}' set to None"


    def test_cant_append_list(self, lambda_context: LambdaContext):
        from util.user.user import User

        username = "test_user"
        user = User(username)

        # Access is a list, so it should be frozen:
        with pytest.raises(AttributeError) as excinfo:
            user.access.append("admin")
        assert "'tuple' object has no attribute 'append'" in str(excinfo.value)

    def test_can_modify_list(self, lambda_context: LambdaContext):
        from util.user.user import User

        username = "test_user"
        user = User(username)

        # Access is a list, so we can modify it:
        assert list(user.access) == ["user"], "Base list is not just 'user'"
        user.access = list(user.access) + ["admin"]
        assert list(user.access) == ["user", "admin"], "Access should now contain 'admin'"
