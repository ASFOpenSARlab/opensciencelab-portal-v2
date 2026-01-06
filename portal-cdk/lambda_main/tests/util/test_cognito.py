import os

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
