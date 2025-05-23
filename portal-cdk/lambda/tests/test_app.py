from dataclasses import dataclass
import time

import main
import pytest
import jwt

BASIC_REQUEST = {
    "rawPath": "/test",
    "requestContext": {
        "requestContext": {"requestId": "227b78aa-779d-47d4-a48e-ce62120393b8"},
        "http": {"method": "GET", "path": "/test"},
        "stage": "$default",
    },
    "cookies": [],
}

BAD_JWT = (
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6ImJsYSJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiw"
    "ibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTc0Nzk1OTY4MiwiZXhwIjoxNzQ3OTY"
    "zMjgyLCJ1c2VybmFtZSI6ImJhZF91c2VyIn0.GzmJ_7GBSMSrbt_HwfDE3Rc8X7O_9oTviC1eHWiDrgc"
)


def validate_jwt(*args, **vargs):
    return {
        "client_id": "2pjp68mov6sfhqda8pjphll8cq",
        "token_use": "access",
        "auth_time": time.time(),
        "exp": time.time() + 100,
        "iat": time.time() - 100,
        "username": "test_user",
    }


def update_item(*args, **vargs):
    return True


def get_event(path="/", method="GET", cookies={}, headers={}):
    ret_event = BASIC_REQUEST

    # Update request path/method
    ret_event["rawPath"] = path
    ret_event["requestContext"]["http"]["path"] = path
    ret_event["requestContext"]["http"]["method"] = method

    for name, value in cookies.items():
        ret_event["cookies"].append(f"{name}={value}")

    return ret_event


@dataclass
class LambdaContext:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = "arn:aws:lambda:eu-west-1:123456789012:function:test"
    aws_request_id: str = "da658bd3-2d6f-4e7b-8ec2-937234644fdc"


@pytest.fixture
def lambda_context() -> LambdaContext:
    return LambdaContext()


class TestPortalFormating:
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

    def test_static_image_dne(self, lambda_context: LambdaContext, monkeypatch):
        event = get_event(path="/static/img/dne.png")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 404

    def test_static_image_bad_type(self, lambda_context: LambdaContext, monkeypatch):
        event = get_event(path="/static/foo/bar.zip")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 404

    def test_static_image(self, lambda_context: LambdaContext, monkeypatch):
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

    def test_bad_jwt(self, lambda_context: LambdaContext, monkeypatch):
        monkeypatch.setattr("util.auth.get_key_validation", lambda: {"bla": "bla"})
        event = get_event(path="/portal", cookies={"portal-jwt": BAD_JWT})
        with pytest.raises(jwt.exceptions.InvalidSignatureError) as excinfo:
            main.lambda_handler(event, lambda_context)
        assert str(excinfo.value) == "Signature verification failed"

    def test_logged_in(self, lambda_context: LambdaContext, monkeypatch):
        # Make JWT validate
        monkeypatch.setattr("util.auth.validate_jwt", validate_jwt)
        monkeypatch.setattr("jwt.decode", validate_jwt)

        # Ignore DB
        monkeypatch.setattr("util.auth.update_item", update_item)

        event = get_event(path="/portal", cookies={"portal-jwt": "bla"})
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Welcome to OpenScienceLab") != -1
        assert ret["headers"].get("Location") is None
        assert ret["headers"].get("Content-Type") == "text/html"

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
