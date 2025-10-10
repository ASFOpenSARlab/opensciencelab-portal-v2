import os
import json

import boto3
from moto import mock_aws

from util.user_ip_logs_stream import send_user_ip_logs, get_user_ip_logs

REGION = os.getenv("STACK_REGION", "us-west-2")
USER_IP_LOGS_GROUP_NAME = "FAKE_USER_IP_LOGS_GROUP_NAME"
USER_IP_LOGS_STREAM_NAME = "FAKE_USER_IP_LOGS_STREAM_NAME"


@mock_aws
class TestUserIpLogsClass:
    def setup_class():
        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util

        util.user_ip_logs_stream._logs_client = boto3.client("logs", region_name=REGION)

    def setup_method(self, method):
        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util

        self.message = {"username": "fakeuser"}

        util.user_ip_logs_stream._logs_client.create_log_group(
            logGroupName=USER_IP_LOGS_GROUP_NAME
        )

        util.user_ip_logs_stream._logs_client.create_log_stream(
            logGroupName=USER_IP_LOGS_GROUP_NAME, logStreamName=USER_IP_LOGS_STREAM_NAME
        )

        self.logs_client = util.user_ip_logs_stream._logs_client

    def test_user_ip_log_send_success(self, monkeypatch):
        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)

        # Send fake log to fake cloudwatch log group
        ret = send_user_ip_logs(self.message)

        assert ret != {}

        # Check if log exists in group
        response = self.logs_client.get_log_events(
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

        # Send fake log to fake cloudwatch log group
        ret = send_user_ip_logs(self.message)

        assert ret == {}

        # Check if log exists in group
        response = self.logs_client.get_log_events(
            logGroupName=USER_IP_LOGS_GROUP_NAME,
            logStreamName=USER_IP_LOGS_STREAM_NAME,
            startFromHead=True,
        )

        assert response["events"] == []

    def test_user_get_logs_from_cloudwatch(self, monkeypatch):
        monkeypatch.setenv("USER_IP_LOGS_GROUP_NAME", USER_IP_LOGS_GROUP_NAME)
        monkeypatch.setenv("USER_IP_LOGS_STREAM_NAME", USER_IP_LOGS_STREAM_NAME)

        # Send fake log to fake cloudwatch log group
        send_user_ip_logs(self.message)

        # Moto has not implemented creating field indexes.
        # Therefore, we can query for username, etc like we would elsewhere in the code.
        query = "fields @message | filter username like 'fakeuser'"

        results = get_user_ip_logs(query=query)

        assert self.message in results

        print(results)

        assert False
