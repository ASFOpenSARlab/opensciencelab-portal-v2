import json
from base64 import b64encode

import pytest
import jwt
from jwt.algorithms import RSAAlgorithm

import main
from util.auth import PORTAL_USER_COOKIE, COGNITO_JWT_COOKIE


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


class TestPortalAuth:
    def test_generic_error(self, monkeypatch):
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

    def test_auth_no_code(self, lambda_context, helpers):
        event = helpers.get_event(path="/auth")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 401
        assert ret["body"].find("No return Code found.") != -1
        assert not ret["headers"].get("Location")
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_auth_bad_code(
        self, lambda_context, monkeypatch, helpers, mocked_requests_post
    ):
        monkeypatch.setattr("requests.post", mocked_requests_post)
        event = helpers.get_event(path="/auth", qparams={"code": "bad_code"})
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 401
        assert ret["body"].find("Could not complete token exchange") != -1

    def test_auth_good_code(
        self, lambda_context, monkeypatch, helpers, mocked_requests_post
    ):
        # Create FakeUser instance to be monkeypatched in and inspected after modified
        user = helpers.FakeUser()
        monkeypatch.setattr("main.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("requests.post", mocked_requests_post)
        monkeypatch.setattr("util.auth.validate_jwt", helpers.validate_jwt)
        monkeypatch.setattr(
            "aws_lambda_powertools.utilities.parameters.get_secret",
            lambda a: "er9LnqEOiH+JLBsFCy0kVeba6ZSlG903cliU7VYKnM8=",
        )

        event = helpers.get_event(
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
        assert user.last_cookie_assignment == "2024-01-01 12:00:00"

    def test_bad_jwt(self, lambda_context, monkeypatch, helpers):
        monkeypatch.setattr("util.auth.get_key_validation", lambda: {"bla": "bla"})
        monkeypatch.setattr(
            "util.auth.refresh_map",
            lambda *args, **kwargs: {
                "access_token": BAD_JWT,
                "id_token": {"email": "bla@bla.com"},
            },
        )
        event = helpers.get_event(path="/portal", cookies={"portal-jwt": BAD_JWT})
        with pytest.raises(jwt.exceptions.InvalidAlgorithmError) as excinfo:
            main.lambda_handler(event, lambda_context)
        assert str(excinfo.value) == "The specified alg value is not allowed"

    def test_old_jwt(self, lambda_context, monkeypatch, helpers):
        jwk_string = RSAAlgorithm.from_jwk(json.dumps(JWK))

        monkeypatch.setattr(
            "util.auth.refresh_map",
            lambda *args, **kwargs: {
                "access_token": OLD_JWT,
                "id_token": {"email": "bla@bla.com"},
            },
        )
        monkeypatch.setattr(
            "util.auth.get_key_validation",
            lambda: {
                "KBEg4O96Pyyn2k7fcKdl5Lf9OZBITSyKTjGpKPtymDU=": jwk_string,
            },
        )
        event = helpers.get_event(
            path="/portal/profile/form/joe", cookies={"portal-jwt": OLD_JWT}
        )
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["body"] == "User is not logged in"
        assert (
            ret["headers"].get("Location").endswith("?return=/portal/profile/form/joe")
        )
        # Make sure we're setting cookies to an empty value
        assert ret["cookies"][0].find("Expires") != -1

    def test_post_portal_hub_auth(
        self, lambda_context, fake_auth, helpers, monkeypatch
    ):
        # Create FakeUser instance to be monkeypatched in and inspected after modified
        user = helpers.FakeUser()
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        body_payload = json.dumps({"username": "test_user"})
        event = helpers.get_event(
            path="/portal/hub/auth",
            method="POST",
            body=b64encode(body_payload.encode("ascii")),
            cookies=fake_auth,
        )
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "application/json"
        json_payload = json.loads(ret["body"])
        assert json_payload.get("message") == "OK"
        assert json_payload.get("data")

    def test_get_portal_hub_auth(self, lambda_context, fake_auth, helpers, monkeypatch):
        # Create FakeUser instance to be monkeypatched in and inspected after modified
        user = helpers.FakeUser()
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(path="/portal/hub/login", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "text/html"
        assert ret["body"].find("hello - Cookie Created") != -1
        cookies = [cookie.split("=")[0] for cookie in ret["cookies"]]
        assert PORTAL_USER_COOKIE in cookies

    def test_get_portal_hub_no_auth(self, lambda_context, helpers):
        event = helpers.get_event(path="/portal/hub", cookies={"foo": "bar"})
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["body"] == "User is not logged in"
        assert ret["headers"].get("Location").endswith("?return=/portal/hub")
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_logged_in(self, lambda_context, fake_auth, helpers, monkeypatch):
        user = helpers.FakeUser()
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Welcome to OpenScienceLab") != -1
        assert ret["headers"].get("Location") is None
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_users_logged_in_root_forward(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(path="/", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["body"] == "Redirecting to Portal"
        assert ret["headers"].get("Location") == "/portal"

    def test_log_out(self, lambda_context, helpers):
        event = helpers.get_event(path="/logout")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        # Make sure we've been logged out
        assert ret["body"].find("You have been logged out") != -1
        # And cookies are being expired
        assert ret["cookies"][0].find("Expires") != -1
        assert ret["cookies"][1].find("Expires") != -1
        # And user is redirected to home page
        assert ret["headers"].get("Location") == "/"
