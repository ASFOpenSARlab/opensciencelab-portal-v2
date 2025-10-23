import os
import json
from base64 import b64encode

import boto3
from moto import mock_aws

from util.auth import encrypt_data
import main

REGION = os.getenv("STACK_REGION", "us-west-2")
EMAIL_DOMAIN = "my.test.domain.com"


@mock_aws
class TestHubPages:
    def setup_method(self, method):
        # Create verified domain
        # https://stackoverflow.com/questions/77356259/moto-mock-ses-list-identitiesidentitytype-emailaddress-returns-both-email-ad
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html#client
        # Note that SESv2 currently does not mock domain verification thus we will use SESv1
        ses: boto3.client = boto3.client("ses", region_name=REGION)
        ses.verify_email_identity(EmailAddress="test_user@user.com")
        ses.verify_domain_dkim(Domain=EMAIL_DOMAIN)

        self.ses_v2: boto3.client = boto3.client("sesv2", region_name=REGION)

    def test_hub_send_email_success(
        self, monkeypatch, lambda_context, helpers, fake_get_secret
    ):
        monkeypatch.setenv("SES_EMAIL", f"testing@{EMAIL_DOMAIN}")
        monkeypatch.setenv("SES_DOMAIN", EMAIL_DOMAIN)
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.hub.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.hub.send_email._sesv2", self.ses_v2)
        monkeypatch.setattr("portal.hub.send_email.User", lambda *args, **kwargs: user)

        user_email = user.email
        user_username = user.username

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
        encrypted_payload: str = encrypt_data(payload)

        # The helpers.get_event() does not base64 encode the payload
        encoded_payload: bytes = b64encode(encrypted_payload.encode("utf-8"))

        # Send payload
        event = helpers.get_event(
            path="/portal/hub/user/email",
            method="POST",
            # cookies=fake_auth,
            body=encoded_payload,
        )

        ret = main.lambda_handler(event, lambda_context)
        response = json.loads(ret["body"])

        assert ret["statusCode"] == 200
        assert response["result"] == "Success"
        assert "reason" not in response

    def test_hub_send_email_bad_payload(
        self, monkeypatch, lambda_context, helpers, fake_get_secret
    ):
        monkeypatch.setenv("SES_EMAIL", f"testing@{EMAIL_DOMAIN}")
        monkeypatch.setenv("SES_DOMAIN", EMAIL_DOMAIN)
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.hub.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.hub.send_email._sesv2", self.ses_v2)
        monkeypatch.setattr("portal.hub.send_email.User", lambda *args, **kwargs: user)

        # Create payload to send to endpoint
        payload = {}

        # Encrypt payload
        encrypted_payload = encrypt_data(payload)

        # The helpers.get_event() does not base64 encode the payload
        encoded_payload: bytes = b64encode(encrypted_payload.encode("utf-8"))

        # Send payload
        event = helpers.get_event(
            path="/portal/hub/user/email",
            method="POST",
            # cookies=fake_auth,
            body=encoded_payload,
        )

        ret = main.lambda_handler(event, lambda_context)
        response = json.loads(ret["body"])
        assert ret["statusCode"] == 422
        assert response["result"] == "Error"
        assert response["reason"] == "KeyError('to')"
