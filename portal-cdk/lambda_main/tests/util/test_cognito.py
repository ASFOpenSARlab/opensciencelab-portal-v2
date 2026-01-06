import os
from datetime import datetime
import pytz

from moto import mock_aws
import boto3

REGION = os.getenv("STACK_REGION", "us-west-2")
TEST_USER_PASSWORD = "This_Is_Test_Users_Password_9"


@mock_aws
class TestCognitoClass:
    def setup_class():
        import util

        util.cognito._COGNITO_CLIENT = boto3.client("cognito-idp", region_name=REGION)

    def setup_method(self, method):
        import util

        # Mock the user pool
        mock_up = util.cognito._COGNITO_CLIENT.create_user_pool(PoolName="MockUserPool")
        mock_up_id = mock_up["UserPool"]["Id"]

        # Add custom attributes:
        util.cognito._COGNITO_CLIENT.add_custom_attributes(
            UserPoolId=mock_up_id,
            CustomAttributes=[
                {
                    "Name": "mfa_reset_code",
                    "AttributeDataType": "String",
                    "Mutable": True,
                    "Required": False,
                    "StringAttributeConstraints": {
                        "MinLength": "10",
                        "MaxLength": "10",
                    },
                },
                {
                    "Name": "mfa_reset_date",
                    "AttributeDataType": "DateTime",
                    "Mutable": True,
                    "Required": False,
                },
            ],
        )

        # Mock the Client
        mock_upc = util.cognito._COGNITO_CLIENT.create_user_pool_client(
            UserPoolId=mock_up_id, ClientName="MockUserPoolClient"
        )
        mock_upc_client = mock_upc["UserPoolClient"]["ClientId"]

        # Mock the Domain
        mock_upc_domain = "MockDomain"
        util.cognito._COGNITO_CLIENT.create_user_pool_domain(
            Domain=mock_upc_domain,
            UserPoolId=mock_up_id,
        )

        # Create an empty user
        util.cognito._COGNITO_CLIENT.admin_create_user(
            UserPoolId=mock_up_id,
            Username="test_user",
            TemporaryPassword=TEST_USER_PASSWORD,
        )

        # Back populate values
        util.cognito.COGNITO_POOL_ID = mock_up_id
        util.cognito.COGNITO_CLIENT_ID = mock_upc_client
        util.cognito.COGNITO_DOMAIN_ID = mock_upc_domain

    def test_get_user(self):
        from util.cognito import get_user_from_user_pool

        dne_user = get_user_from_user_pool("dne_user")
        assert not dne_user.get("Username")

        test_user = get_user_from_user_pool("test_user")
        assert test_user.get("Username") == "test_user"

    def test_delete_user(self):
        from util.cognito import delete_user_from_user_pool, get_user_from_user_pool

        assert not delete_user_from_user_pool("dne_user")

        assert delete_user_from_user_pool("test_user")

        assert not get_user_from_user_pool("test_user")

    def test_user_password_validation(self):
        from util.cognito import verify_user_password

        assert verify_user_password("test_user", TEST_USER_PASSWORD)

        assert not verify_user_password("test_user", "KnownBad")

        assert not verify_user_password("dne_user", TEST_USER_PASSWORD)

    def test_set_cognito_user_password(self):
        from util.cognito import set_cognito_user_password, verify_user_password

        assert not set_cognito_user_password("dne_user", "bad_pass")

        assert verify_user_password("test_user", TEST_USER_PASSWORD)

        assert set_cognito_user_password("test_user", TEST_USER_PASSWORD + "_padding")

        assert not verify_user_password("test_user", TEST_USER_PASSWORD)

        assert verify_user_password("test_user", TEST_USER_PASSWORD + "_padding")

    def test_user_mfa_reset(self):
        from util.cognito import verify_user_password, reset_user_mfa

        assert not reset_user_mfa("dne_user")

        # reset user to unknown password
        reset_user_mfa("test_user")
        assert not verify_user_password("test_user", TEST_USER_PASSWORD)

        # reset user to known password
        reset_user_mfa("test_user", TEST_USER_PASSWORD)
        assert verify_user_password("test_user", TEST_USER_PASSWORD)

    def test_get_set_cognito_user_attribute(self):
        from util.cognito import get_cognito_user_attribute, set_cognito_user_attribute

        assert get_cognito_user_attribute("dne_user", "mfa_reset_code") is False
        assert get_cognito_user_attribute("test_user", "mfa_reset_code") is None

        # Moto does NOT respect format/constraints
        # assert not set_cognito_user_attribute("test_user", "mfa_reset_code", "1")
        # assert not set_cognito_user_attribute("test_user", "mfa_reset_date", "bla")

        assert set_cognito_user_attribute("test_user", "mfa_reset_code", "1234567890")
        assert get_cognito_user_attribute("test_user", "mfa_reset_code") == "1234567890"
        assert (
            not get_cognito_user_attribute("test_user", "mfa_reset_code")
            == "badcodevalue"
        )
        assert set_cognito_user_attribute("test_user", "mfa_reset_code")
        assert get_cognito_user_attribute("test_user", "mfa_reset_code") is None

        current_time = datetime.now(pytz.UTC).replace(microsecond=0)
        assert set_cognito_user_attribute("test_user", "mfa_reset_date", current_time)
        assert get_cognito_user_attribute("test_user", "mfa_reset_date") == current_time
        assert get_cognito_user_attribute("test_user", "mfa_reset_date") < datetime.now(
            pytz.UTC
        )

    def test_reset_mfa_with_password(self):
        from util.cognito import (
            set_mfa_reset_values,
            reset_user_mfa_with_password,
            verify_user_password,
            get_cognito_user_attribute,
        )

        assert not reset_user_mfa_with_password("test_user", "badpass", "badcode")

        # Make sure we know the right password
        assert verify_user_password("test_user", TEST_USER_PASSWORD)
        assert not verify_user_password("test_user", "badpassword")

        # Set up a reset validation
        set_mfa_reset_values("test_user", "1234567890")

        # test resetting
        assert not reset_user_mfa_with_password("test_user", "badpass", "badcode")
        assert not reset_user_mfa_with_password("test_user", TEST_USER_PASSWORD, "1")
        assert reset_user_mfa_with_password(
            "test_user", TEST_USER_PASSWORD, "1234567890"
        )

        # Confirm user has been recreated w/ password
        assert verify_user_password("test_user", TEST_USER_PASSWORD)
        assert get_cognito_user_attribute("test_user", "mfa_reset_code") is None
