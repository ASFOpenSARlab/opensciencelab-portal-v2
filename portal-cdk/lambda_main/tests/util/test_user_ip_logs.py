import os
import json

import boto3
from moto import mock_aws

from util.user_ip_logs_stream import send_user_ip_logs

REGION = os.getenv("STACK_REGION", "us-west-2")
USER_IP_LOGS_GROUP_NAME = "FAKE_USER_IP_LOGS_GROUP_NAME"
USER_IP_LOGS_STREAM_NAME = "FAKE_USER_IP_LOGS_STREAM_NAME"


@mock_aws
class TestUserIpLogsClass:
    def setup_class():
        pass

    def setup_method(self, method):
        self.message = {"value": "test"}

        self.logs = boto3.client("logs", region_name=REGION)
        _ = self.logs.create_log_group(logGroupName=USER_IP_LOGS_GROUP_NAME)

        _ = self.logs.create_log_stream(
            logGroupName=USER_IP_LOGS_GROUP_NAME, logStreamName=USER_IP_LOGS_STREAM_NAME
        )

    def test_user_ip_log_send_success(self, monkeypatch):
        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)

        monkeypatch.setattr(
            "util.user_ip_logs_stream._get_logs_client",
            lambda *args, **kwargs: self.logs,
        )

        # Send fake log to fake cloudwatch log group
        ret = send_user_ip_logs(self.message)

        assert ret != {}

        # Check if log exists in group
        response = self.logs.get_log_events(
            logGroupName=USER_IP_LOGS_GROUP_NAME,
            logStreamName=USER_IP_LOGS_STREAM_NAME,
            startFromHead=True,
        )

        assert len(response["events"]) == 1
        assert response["events"][0]["message"] == json.dumps(self.message)

    def test_user_ip_no_log_group(self, monkeypatch):
        # Unset environements
        monkeypatch.delenv("USER_IP_LOGS_GROUP_NAME", raising=False)
        monkeypatch.delenv("USER_IP_LOGS_STREAM_NAME", raising=False)

        monkeypatch.setattr(
            "util.user_ip_logs_stream._get_logs_client",
            lambda *args, **kwargs: self.logs,
        )

        # Send fake log to fake cloudwatch log group
        ret = send_user_ip_logs(self.message)

        assert ret == {}

        # Check if log exists in group
        response = self.logs.get_log_events(
            logGroupName=USER_IP_LOGS_GROUP_NAME,
            logStreamName=USER_IP_LOGS_STREAM_NAME,
            startFromHead=True,
        )

        assert response["events"] == []
