import os


import boto3
from moto import mock_aws

import main

REGION = os.getenv("STACK_REGION", "us-west-2")
USER_IP_LOGS_GROUP_NAME = "FAKE_USER_IP_LOGS_GROUP_NAME"
USER_IP_LOGS_STREAM_NAME = "FAKE_USER_IP_LOGS_STREAM_NAME"


@mock_aws
class TestProfileAccess:
    def setup_method(self, method):
        # Logs need to be created since the profiles use @require_access which populates the log group
        self.logs_client = boto3.client("logs", region_name=REGION)

        self.logs_client.create_log_group(logGroupName=USER_IP_LOGS_GROUP_NAME)

        self.logs_client.create_log_stream(
            logGroupName=USER_IP_LOGS_GROUP_NAME, logStreamName=USER_IP_LOGS_STREAM_NAME
        )

    # Test user accessing other profile
    def test_user_access_other_profile(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal/profile/form/other_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "\"{'Redirect to /portal/profile/form/test_user'}\""
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    # Test user accessing own profile
    def test_user_access_own_profile(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)
        monkeypatch.setattr("util.user_ip_logs_stream._logs_client", self.logs_client)

        path = "/portal/profile/form/test_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Hello <i>test_user</i>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"

    # Test user redirect for required profile filling
    def test_user_profile_redirect_flag(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True)
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User must update profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    # Test user accessing other profile while required to fill own profile
    def test_user_access_other_profile_must_fill_own(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True)
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)
        monkeypatch.setattr("util.user_ip_logs_stream._logs_client", self.logs_client)

        path = "/portal/profile/form/test_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Hello <i>test_user</i>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"

    # Test admin accessing other profile
    def test_admin_access_other_profile(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        admin_user = helpers.FakeUser(username="admin_user", access=["admin", "user"])
        profile_user = helpers.FakeUser(username="other_user", access=["user"])

        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: admin_user)
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: profile_user)

        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)
        monkeypatch.setattr("util.user_ip_logs_stream._logs_client", self.logs_client)

        path = "/portal/profile/form/other_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Hello <i>other_user</i>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"
        # Admin should see settings for other_user:
        assert ret["body"].find("Admin Settings") > -1

    # Test admin redirect for required profile filling
    def test_admin_profile_redirect_flag(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True, access=["admin", "user"])
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User must update profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    # Test admin accessing other profile while required to fill own profile
    def test_admin_access_other_profile_must_fill_own(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True, access=["admin", "user"])
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal/profile/form/other_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User must update profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    def test_normal_user_no_table(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)
        monkeypatch.setattr("util.user_ip_logs_stream._logs_client", self.logs_client)

        event = helpers.get_event(
            path="/portal/profile/form/test_user", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert not ret["headers"].get("Location")
        assert ret["body"].find("Admin Settings") == -1

    def test_admin_user_with_table(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["user", "admin"])

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)
        monkeypatch.setattr("util.user_ip_logs_stream._logs_client", self.logs_client)

        event = helpers.get_event(
            path="/portal/profile/form/test_user", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["body"].find("Admin Settings") > -1
