from base64 import b64encode
import json

import main
from conftest import MockResponse
import logging


class TestRenderingMfaTemplates:
    # Ensure MFA page is not reachable if not logged in
    def test_mfa_form(self, lambda_context, helpers):
        event = helpers.get_event(path="/mfa")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200

    def test_mfa_form_submit(self, lambda_context, helpers, monkeypatch):
        monkeypatch.setattr(
            "portal.mfa.verify_user_password", lambda *args, **kwargs: False
        )

        monkeypatch.setattr(
            "portal.mfa.submit_captcha_challenge", lambda *args, **kwargs: 1.0
        )
        monkeypatch.setenv("RECAPTCHA_THRESHOLD", "0.5")

        post_params = "username=test&password=test"
        event = helpers.get_event(
            path="/mfa/reset",
            body=b64encode(post_params.encode("ascii")),
            method="POST",
        )
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200

    def test_mfa_email_failure(self, lambda_context, helpers, monkeypatch):
        # Verify that broken email sending get reported to user
        monkeypatch.setattr(
            "portal.mfa.verify_user_password", lambda *args, **kwargs: True
        )
        monkeypatch.setattr(
            "portal.mfa.set_mfa_reset_values", lambda *args, **kwargs: True
        )
        monkeypatch.setattr(
            "portal.mfa.get_cognito_user_attribute",
            lambda *args, **kwargs: "bla@bla.com",
        )
        monkeypatch.setattr(
            "portal.mfa.send_email.send_user_email",
            lambda *args, **kwargs: ("Error", "Thinks are broken."),
        )
        monkeypatch.setattr(
            "portal.mfa.submit_captcha_challenge", lambda *args, **kwargs: 1.0
        )
        monkeypatch.setenv("RECAPTCHA_THRESHOLD", "0.5")

        def post_request_response(*args, **kwargs) -> MockResponse:
            data = {
                "success": True,
                "score": 0.9,
            }
            return MockResponse(
                status_code=200,
                text_data=json.dumps(data),
                json_data=data,
            )

        post_params = "username=test&password=test"
        event = helpers.get_event(
            path="/mfa/reset",
            body=b64encode(post_params.encode("ascii")),
            method="POST",
        )
        ret = main.lambda_handler(event, lambda_context)
        assert ret["body"].find("Could not send MFA Reset email") != -1

        # And make sure it doesn't happen when email works
        monkeypatch.setattr(
            "portal.mfa.send_email.send_user_email",
            lambda *args, **kwargs: ("Success", "Email Sent"),
        )

        ret = main.lambda_handler(event, lambda_context)
        assert ret["body"].find("Could not send MFA Reset email") == -1

    def test_mfa_recaptcha_reject_false_credentials(
        self, lambda_context, helpers, monkeypatch, caplog
    ):
        monkeypatch.setattr(
            "portal.mfa.verify_user_password", lambda *args, **kwargs: False
        )

        monkeypatch.setattr(
            "portal.mfa.submit_captcha_challenge", lambda *args, **kwargs: 0.2
        )
        monkeypatch.setenv("RECAPTCHA_THRESHOLD", "0.5")

        post_params = "username=test&password=test"
        with caplog.at_level(logging.INFO, logger="myapp"):
            event = helpers.get_event(
                path="/mfa/reset",
                body=b64encode(post_params.encode("ascii")),
                method="POST",
            )
            ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert (
            ret["body"].find('<p class="warning">Username or Password not found.</p>')
            != -1
        )
        assert "{'response': 'Likely bot detected'}" in caplog.text

    def test_mfa_recaptcha_reject_correct_credentials(
        self, lambda_context, helpers, monkeypatch, caplog
    ):
        monkeypatch.setattr(
            "portal.mfa.verify_user_password", lambda *args, **kwargs: True
        )

        monkeypatch.setattr(
            "portal.mfa.submit_captcha_challenge", lambda *args, **kwargs: 0.2
        )
        monkeypatch.setenv("RECAPTCHA_THRESHOLD", "0.5")

        post_params = "username=test&password=test"
        with caplog.at_level(logging.INFO, logger="myapp"):
            event = helpers.get_event(
                path="/mfa/reset",
                body=b64encode(post_params.encode("ascii")),
                method="POST",
            )
            ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert (
            ret["body"].find('<p class="warning">Username or Password not found.</p>')
            != -1
        )
        assert "{'response': 'Likely bot detected'}" in caplog.text
