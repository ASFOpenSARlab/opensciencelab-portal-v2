import pytest

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
