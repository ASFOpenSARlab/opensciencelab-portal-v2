import os

from moto import mock_aws
import boto3

REGION = os.getenv("STACK_REGION", "us-west-2")


@mock_aws
class TestSESClass:
    def setup_class():
        pass

    def setup_method(self, method):
        self.sesv2 = boto3.client("sesv2", region_name=REGION)
        self.verified_email_address = "test@example.com"

    def test_user_verified(self):
        response = self.sesv2.create_email_identity(
            EmailIdentity=self.verified_email_address
        )

        # Assert that the response indicates success.
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Verify the identity was created by listing identities.
        identities_list = self.sesv2.list_email_identities()
        assert self.verified_email_address in [
            ident["IdentityName"] for ident in identities_list["EmailIdentities"]
        ]

    def test_send_email(self):
        pass
