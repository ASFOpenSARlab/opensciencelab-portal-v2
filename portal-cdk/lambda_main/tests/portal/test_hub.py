from util.auth import encrypt_data
import main


class TestHubPages:
    def test_hub_send_email(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser()
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
