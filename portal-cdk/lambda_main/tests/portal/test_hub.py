import os

import boto3
from moto import mock_aws

from util.auth import encrypt_data
import main

REGION = os.getenv("STACK_REGION", "us-west-2")
EMAIL_DOMAIN = "opensciencelab.asf.alaska.edu"


@mock_aws
class TestHubPages:
    def setup_method(self, method):
        # Create verified domain
        # https://stackoverflow.com/questions/77356259/moto-mock-ses-list-identitiesidentitytype-emailaddress-returns-both-email-ad
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html#client
        # Note that SESv2 currently does not mock domain verification thus we will use SESv1
        ses: boto3.Client = boto3.client("ses", region_name=REGION)
        ses.verify_email_identity(EmailAddress="test_user@user.com")
        ses.verify_domain_dkim(Domain=EMAIL_DOMAIN)

    def test_hub_send_email_success(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.hub.User", lambda *args, **kwargs: user)

        user_email = user.email
        user_username = user.username

        # jwt.decode is patched globally for testing. Depatch so that jwt.decode works as expected.
        monkeypatch.setattr("jwt.decode", helpers.jwt_decode)

        # Create payload to send to endpoint
        payload = {
            "to": {
                "username": [user_username],
                "email": [user_email],
            },
            # "from": {"username": "", "email": ""}, ## Deprecated
            "cc": {
                "username": user_username,
                "email": [user_email],
            },
            "bcc": {
                "username": user_username,
                "email": [user_email],
            },
            "subject": "Test Hub Pages email",
            "html_body": "This is only a test.",
        }

        # Encrypt payload
        encrypted_payload = encrypt_data(payload)

        # Send payload
        event = helpers.get_event(
            path="/portal/hub/user/email",
            method="POST",
            # cookies=fake_auth,
            body=encrypted_payload,
        )

        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"] == '{"result": "Success"}'

    def test_hub_send_email_bad_payload(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.hub.User", lambda *args, **kwargs: user)

        # jwt.decode is patched globally for testing. Depatch so that jwt.decode works as expected.
        monkeypatch.setattr("jwt.decode", helpers.jwt_decode)

        # Create payload to send to endpoint
        payload = {}

        # Encrypt payload
        encrypted_payload = encrypt_data(payload)

        # Send payload
        event = helpers.get_event(
            path="/portal/hub/user/email",
            method="POST",
            # cookies=fake_auth,
            body=encrypted_payload,
        )

        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert ret["body"] == '{"result": "Error"}'
