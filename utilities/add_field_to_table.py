import argparse
import boto3
import os
from typing import Any
import json
from tqdm import tqdm


_DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE = None, None, None

parser = argparse.ArgumentParser(description="Populate a new field in a dynamo table")
_ = parser.add_argument(
    "-t",
    "--dynamo-table-name",
    dest="dynamo_table",
    type=str,
    required=True,
    help="The DynamoDB table name for the migration destination",
)
_ = parser.add_argument(
    "-k",
    "--key",
    dest="key",
    type=str,
    required=True,
    help="The key of the field to be populated",
)
_ = parser.add_argument(
    "-v",
    "--value",
    dest="value",
    type=str,
    required=True,
    help="Json string representation of a generic object",
)
args = parser.parse_args()


def _get_dynamo():
    """
    Lazy load all DynamoDB stuff since it takes forever the first time.
    """
    global _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE  # pylint: disable=global-statement
    region = os.getenv("STACK_REGION", "us-west-2")
    if not _DYNAMO_CLIENT:
        _DYNAMO_CLIENT = boto3.client("dynamodb", region_name=region)
    if not _DYNAMO_DB:
        _DYNAMO_DB = boto3.resource("dynamodb", region_name=region)
    if not _DYNAMO_TABLE:
        _DYNAMO_TABLE = _DYNAMO_DB.Table(args.dynamo_table)
    return _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE


def update_item(partition_key: str, partition_value: str, key: str, value: Any) -> bool:
    """
    Updates an item in the DB.
    """
    _client, _db, table = _get_dynamo()
    table.update_item(
        Key={
            partition_key: partition_value,
        },
        UpdateExpression="SET #key = :value",
        ExpressionAttributeNames={
            "#key": key,
        },
        ExpressionAttributeValues={
            ":value": value,
        },
    )
    return True


def update_table():
    _client, _db, table = _get_dynamo()

    scan_kwargs = {}

    # Get primary key
    primary_key = [
        n["AttributeName"] for n in table.key_schema if n["KeyType"] == "HASH"
    ][0]

    # Get partition keys for each item in table
    total_items = 0
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key

        # Use the Table.scan() method from Boto3
        response = table.scan(**scan_kwargs)

        # Update specified key value in each item in the table
        response_items = response.get("Items", [])
        for item in tqdm(response_items):
            table.update_item(
                Key={
                    primary_key: item[primary_key],
                },
                UpdateExpression="SET #key = :value",
                ExpressionAttributeNames={
                    "#key": args.key,
                },
                ExpressionAttributeValues={
                    ":value": json.loads(args.value),
                },
            )
        total_items += len(response_items)

        start_key = response.get("LastEvaluatedKey", None)
        done = start_key is None
    print(f"{total_items} updated")


if __name__ == "__main__":
    update_table()
