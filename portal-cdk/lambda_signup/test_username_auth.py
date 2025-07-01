import pytest
from . import main

class TestUsernameAuth:
    @pytest.mark.parametrize("username", ["cameron-waz.here", "noSpecials", "test_user"])
    def test_username_auth_valid(self, lambda_context, username):
        validated_username = main.lambda_handler(
            {"userName": username},
            lambda_context,
        )
        # If it got here, you didn't throw. Success!
        # Make sure the function didn't mutate the input
        assert validated_username == {"userName": username}

    @pytest.mark.parametrize("username", ["<script>alert('Injected!');</script>", "some@email.com"])
    def test_username_auth_invalid(self, lambda_context, username):
        with pytest.raises(ValueError) as exc_info:
            main.lambda_handler(
                {"userName": username},
                lambda_context,
            )
            assert str(exc_info.value) == main.ERROR_MESSAGE
