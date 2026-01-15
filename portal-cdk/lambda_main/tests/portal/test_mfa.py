from base64 import b64encode

import main


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
