import json
import os
import time

import boto3

from aws_lambda_powertools import Logger

logger = Logger(log_uncaught_exceptions=True)

_logs = None


def _get_logs_client() -> boto3.client:
    global _logs
    if not _logs:
        _logs = boto3.client("logs", region_name=os.environ.get("region"))
    return _logs


def send_user_ip_logs(message: dict | str) -> dict:
    """
    `message` is either a dict or string of event information to be sent to custom cloudwatch logs.
    """
    if isinstance(message, dict):
        message = json.dumps(message)

    event = {
        "timestamp": int(time.time() * 1000),
        "message": message,
    }

    logs_client = _get_logs_client()

    log_group_name = os.environ.get("USER_IP_LOGS_GROUP_NAME", None)
    log_stream_name = os.environ.get("USER_IP_LOGS_STREAM_NAME", None)

    if not log_group_name or not log_stream_name:
        logger.warning(
            "User Activity Log Group or Stream not defined. Did you set the environment variable?"
        )
        logger.warning("User IP event not collected in special log group. Event: ")
        logger.warning(json.dumps(event))
        return {}

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/put_log_events.html
    response = logs_client.put_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        logEvents=[event],
    )

    return response
