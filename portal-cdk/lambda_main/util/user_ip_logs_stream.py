import json
import os
import time
import datetime

import boto3

from util.user import User
from .exceptions import EnvironmentNotSet

from aws_lambda_powertools import Logger

logger = Logger(log_uncaught_exceptions=True)

_logs_client = None


def _get_logs_client() -> boto3.client:
    global _logs_client
    if not _logs_client:
        _logs_client = boto3.client("logs", region_name=os.environ.get("region"))
    return _logs_client


def update_user_ip_in_db(
    username: str,
    ip_address: str,
    country_code: str,
) -> bool:
    user = User(username)

    user.ip_address = ip_address
    user.country_code = country_code


def send_user_ip_logs(
    username: str,
    ip_address: str,
    country_code: str,
    access_roles: str,
) -> dict:
    event = {
        "timestamp": int(time.time() * 1000),
        "message": json.dumps(
            {
                "username": username,
                "ip_address": ip_address,
                "country_code": country_code,
                "access_roles": access_roles,
            }
        ),
    }

    logs_client = _get_logs_client()

    log_group_name = os.environ.get("USER_IP_LOGS_GROUP_NAME", None)
    log_stream_name = os.environ.get("USER_IP_LOGS_STREAM_NAME", None)

    if not log_group_name or not log_stream_name:
        logger.warning("User IP event not collected in special log group. Event: ")
        logger.warning(json.dumps(event))
        raise EnvironmentNotSet(
            "User Activity Log Group or Stream not defined. Did you set the environment variable?"
        )

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

    Example from test:

        [[{'field': '@ptr', 'value': 1}, {'field': '@message', 'value': '{"username": "fakeuser"}'}], ]

        =>

        [{'@message': '{"username": "fakeuser"}'}, ]

    """

    all_results = []

    for r in results:
        all_results.append(
            {event["field"]: event["value"] for event in r if event["field"] != "@ptr"}
        )

    return all_results


def get_user_ip_logs(
    username: str = None,
    start_date: str | datetime.datetime = None,
    end_date: str | datetime.datetime = None,
    limit: int = None,
    query_override: str = None,
) -> dict:
    """
    username: string. Username to filter query by.
    start_time: datetime object or string in ISO 8601 format. Start of query time.
    end_time: datetime object or string in ISO 8601 format. End of query time.
    limit: int between 0-10,000. Number of results rows to return.
    query_override: string. Query to run. Args username and limit are ignored. Useful mainly when fields cannot be indexed.
    """

    username_filter = ""
    if username:
        # If username has wrapped in quotes it will break the query. So strip any quotes.
        username = username.strip('"').strip("'").lower()
        username_filter = f" | filter username = '{username}'"

    limit_filter = ""
    if limit:
        limit = int(limit)
        if limit < 0 or limit > 10000:
            raise ValueError("Parameter `limit` must be between 0 and 10000.")
        limit_filter = f"| limit {limit}"

    if query_override:
        query = str(query_override).strip()
    else:
        query = f"""
            display @timestamp, username, ip_address, country_code, access_roles
            | sort @timestamp desc
            {username_filter}
            {limit_filter}
        """.strip()

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
        raise EnvironmentNotSet(
            "User Activity Log Group or Stream not defined. Did you set the environment variable?"
        )

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
            f"No results returned. Are you sure the query '{query}' is correct?"
        )
        return []

    return _consolidate_results(results)
