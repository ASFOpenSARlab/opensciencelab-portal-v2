import json
import os
import time
import datetime

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


def get_user_ip_logs(
    query: str, start_date: datetime.datetime = None, end_date: datetime.datetime = None
) -> dict:
    if not end_date:
        end_date = datetime.datetime.now(datetime.timezone.utc)
    end_date_int = int(end_date.timestamp())

    if not start_date:
        start_date = end_date - datetime.timedelta(days=30)
    start_date_int = int(start_date.timestamp())

    logs_client = _get_logs_client()

    log_group_name = os.environ.get("USER_IP_LOGS_GROUP_NAME", None)
    log_stream_name = os.environ.get("USER_IP_LOGS_STREAM_NAME", None)

    if not log_group_name or not log_stream_name:
        logger.warning(
            "User Activity Log Group or Stream not defined. Did you set the environment variable?"
        )
        return {}

    start_query_response = logs_client.start_query(
        logGroupName=log_group_name,
        startTime=start_date_int,
        endTime=end_date_int,
        queryString=query,
    )

    query_id = start_query_response["queryId"]

    response = None

    time_to_wait = 0

    while response == None or response["status"] == "Running":
        print("Waiting for query to complete ...")
        time.sleep(time_to_wait)
        response = logs_client.get_query_results(queryId=query_id)

    return response["results"]
