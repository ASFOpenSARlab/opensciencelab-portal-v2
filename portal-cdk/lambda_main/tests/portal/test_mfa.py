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
