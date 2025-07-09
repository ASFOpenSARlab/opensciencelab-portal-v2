"""File of helpers for interacting with DynamoDB."""

import datetime
import os
import json

from cachetools import TTLCache
import boto3
from boto3.dynamodb.conditions import Attr


_DYNAMO_CLIENT = None
_DYNAMO_DB = None
_DYNAMO_TABLE = None


# Keys that this module manages, that you don't want the rest of the code messing with.
RESTRICTED_KEYS = ["username", "created_at", "last_update"]

# Profile cache, upto 100 items, max life 5mins
PROFILE_CACHE = TTLCache(maxsize=100, ttl=5 * 60)


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
        _DYNAMO_TABLE = _DYNAMO_DB.Table(os.getenv("DYNAMO_TABLE_NAME"))
    return _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE


def _remove_restricted_keys(item: dict):
    for key in RESTRICTED_KEYS:
        if key in item:
            del item[key]


def is_cached(username: str) -> bool:
    if username in PROFILE_CACHE:
        return True


def get_cache(username: str) -> dict | None:
    if is_cached(username):
        return PROFILE_CACHE[username]
    return None


def _del_cache(username: str) -> bool:
    if is_cached(username):
        del PROFILE_CACHE[username]
        return True
    return False


def _add_cache(username: str, item: dict) -> dict:
    # Don't cache restricted keys, they are for internal use only.
    _remove_restricted_keys(item)
    PROFILE_CACHE[username] = item
    return item


def alpha(s: str) -> str:
    """
    Only returns the alpha parts of a string.
    """
    return "".join(filter(str.isalnum, s))


def create_item(username: str, item: dict) -> bool:
    """
    Creates an item in the DB.
    """
    _client, _db, table = _get_dynamo()
    # "Cast" to a plain dict, so it can be serialized to JSON.
    item = json.loads(json.dumps(item, default=str))
    for restricted_key in RESTRICTED_KEYS:
        if restricted_key in item:
            raise ValueError(
                f"Can't set '{restricted_key}', that's one we set automatically and WILL get overridden."
            )
    item["username"] = username
    item["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table.put_item(Item=item)

    # Add new item to profile cache
    _add_cache(username, item)

    return True


def get_item(username: str) -> dict:
    """
    Returns an item from the DB, or False if it doesn't exist.
    """
    # Check profile cache
    if is_cached(username):
        return get_cache(username)

    _client, _db, table = _get_dynamo()
    response = table.get_item(Key={"username": username})
    if "Item" in response:
        # Add response to cache & Return
        return _add_cache(username, response["Item"])
    return False


def get_all_items() -> list:
    """
    Returns all items in the DB.
    Need to page because there's a 100 item limit.
    """
    _client, _db, table = _get_dynamo()
    response = table.scan()
    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    return items


def update_item(username: str, updates: dict) -> bool:
    """
    Updates fields in an existing item. (Will create fields if they don't exist.)

    updates: dict, each key-value pair is a different field that'll be updated. fields not
    listed will be left alone.
    """
    _client, _db, table = _get_dynamo()
    # "Cast" to a plain dict, so it can be serialized to JSON.
    updates = json.loads(json.dumps(updates, default=str))
    ### Fail fast if it doesn't exist, they should call create_item instead:
    if not get_item(username):
        return False
    ### Otherwise craft the boto3 update item call:
    updates["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # The '#var' is ID for the keys:
    expression_attribute_names = {f"#{alpha(k)}": k for k in updates.keys()}
    # The ':var' is ID for the values:
    expression_attribute_values = {f":{alpha(k)}": v for k, v in updates.items()}
    update_expression = "SET " + ", ".join(
        # Set the ID for #var and :var equal to each other:
        # (It'll look up the real value in the map above.)
        [f"#{alpha(k)}=:{alpha(k)}" for k in updates.keys()]
    )
    table.update_item(
        Key={"username": username},
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        UpdateExpression=update_expression,
    )

    # Profile was mutated, lets invalidate
    _del_cache(username)

    return True


def delete_item(username: str) -> None:
    """
    Deletes an item from the DB & Cache.
    """
    _client, _db, table = _get_dynamo()
    _del_cache(username)
    table.delete_item(Key={"username": username})


def update_username(old_username: str, new_username: str) -> bool:
    """
    Updates the username of an item in the DB.
    Since it's the primary key, you can't update it directly.
    Returns Bool: if old_username existed in DB already.
    """
    _client, _db, table = _get_dynamo()
    item = get_item(old_username)
    if item:
        item["username"] = new_username
        table.put_item(Item=item)
        delete_item(old_username)
        return True
    return False


# Returns a list of users usernames that have access to a given lab
def list_users_with_lab(lab_short_name: str) -> list[str]:
    _client, _db, table = _get_dynamo()
    filterexpr = Attr("labs").contains(lab_short_name)
    response = table.scan(FilterExpression=filterexpr)

    users = []
    for item in response["Items"]:
        users.append(item["username"])
    return users
