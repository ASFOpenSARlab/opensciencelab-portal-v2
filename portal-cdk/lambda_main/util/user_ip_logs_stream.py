import json
import os
import time
import datetime

import boto3

from aws_lambda_powertools import Logger

logger = Logger(log_uncaught_exceptions=True)

_logs_client = None


def _get_logs_client() -> boto3.client:
    global _logs_client
    if not _logs_client:
        _logs_client = boto3.client("logs", region_name=os.environ.get("region"))
    return _logs_client


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


def _consolidate_results(results: list) -> dict:
    """
    Reformat CloudWatch Query results into a more usuable format.
    Drop "@ptr" field and convert field/values into dictionaries.

    [[{'field': '@ptr', 'value': 1}, {'field': '@message', 'value': '{"username": "fakeuser"}'}], ]

    =>

    [{'@message': '{"username": "fakeuser"}'}, ]

    """

    all_results = []

    for r in results:
        all_results.extend(
            [
                {event["field"]: event["value"]}
                for event in r
                if event["field"] != "@ptr"
            ]
        )

    return all_results


def get_user_ip_logs(
    query: str,
    start_date: str | datetime.datetime = None,
    end_date: str | datetime.datetime = None,
) -> dict:
    """
    start_time: datetime object or string in ISO 8601 format. Start of query time.
    end_time: datetime object or string in ISO 8601 format. End of query time.
    """

    print(f"{query=}, {start_date=}, {end_date=}")

    if type(end_date) is str:
        end_date = datetime.datetime.fromisoformat(end_date.strip('"').strip("'"))

    if type(start_date) is str:
        start_date = datetime.datetime.fromisoformat(start_date.strip('"').strip("'"))

    if not end_date:
        # End query 5 minutes into the future to guarantee that all results are returned.
        end_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=5
        )

    if not start_date:
        # Default start time is 30 days in the past from now
        start_date = end_date - datetime.timedelta(days=30)

    end_date_int = int(end_date.timestamp())
    start_date_int = int(start_date.timestamp())

    logs_client = _get_logs_client()

    log_group_name = os.environ.get("USER_IP_LOGS_GROUP_NAME", None)
    log_stream_name = os.environ.get("USER_IP_LOGS_STREAM_NAME", None)

    if not log_group_name or not log_stream_name:
        logger.warning(
            "User Activity Log Group or Stream not defined. Did you set the environment variable?"
        )
        return {}

    # https://boto3.amazonaws.com/v1/documentation/api/1.26.82/reference/services/logs/client/start_query.html
    start_query_response = logs_client.start_query(
        logGroupName=log_group_name,
        startTime=start_date_int,
        endTime=end_date_int,
        queryString=query,
    )

    query_id = start_query_response["queryId"]

    response = {}

    while response.get("status", None) not in [
        "Cancelled",
        "Complete",
        "Failed",
        "Timeout",
        "Unknown",
    ]:
        time.sleep(1)
        # https://boto3.amazonaws.com/v1/documentation/api/1.26.82/reference/services/logs/client/get_query_results.html
        response = logs_client.get_query_results(queryId=query_id)

    results = response["results"]

    if not results:
        logger.warning(
            "No results returned. Are you sure the query '{query}' is correct?"
        )
        return []

    return _consolidate_results(results)
