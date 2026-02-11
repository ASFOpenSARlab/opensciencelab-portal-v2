"""File of helpers for interacting with DynamoDB."""

import datetime
import os
import json

from cachetools import TTLCache
import boto3
from boto3.dynamodb.conditions import Attr

from util.log_timer import measure_time

from aws_lambda_powertools import Logger


logger = Logger(child=True)

_DYNAMO_CLIENT = None
_DYNAMO_DB = None
_DYNAMO_TABLE_USER = None
_DYNAMO_TABLE_LAB = None
_DYNAMO_TABLE_REQ = None


# Keys that this module manages, that you don't want the rest of the code messing with.
# Todo: Consider moving this to object specific location
RESTRICTED_KEYS = {
    "user": ["username", "created_at", "last_update"],
    "lab": ["labname", "created_at", "last_update"],
    "request": ["labname", "username"],
}

# Table caches, upto 100 items, max life 5mins
# If no record, don't cache!
CACHES = {
    "user": TTLCache(maxsize=100, ttl=5 * 60),
    "lab": TTLCache(maxsize=100, ttl=5 * 60),
}


# TODO: Remove default table name eventually.
def _get_dynamo(table_id: str):
    """
    Lazy load all DynamoDB stuff since it takes forever the first time.
    """
    global _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE_USER, _DYNAMO_TABLE_LAB, _DYNAMO_TABLE_REQ  # pylint: disable=global-statement
    region = os.getenv("STACK_REGION", "us-west-2")
    if not _DYNAMO_CLIENT:
        _DYNAMO_CLIENT = boto3.client("dynamodb", region_name=region)
    if not _DYNAMO_DB:
        _DYNAMO_DB = boto3.resource("dynamodb", region_name=region)
    if not _DYNAMO_TABLE_USER:
        _DYNAMO_TABLE_USER = _DYNAMO_DB.Table(os.getenv("DYNAMO_TABLE_USER_NAME"))
    if not _DYNAMO_TABLE_LAB:
        _DYNAMO_TABLE_LAB = _DYNAMO_DB.Table(os.getenv("DYNAMO_TABLE_LAB_NAME"))
    if not _DYNAMO_TABLE_REQ:
        _DYNAMO_TABLE_REQ = _DYNAMO_DB.Table(os.getenv("DYNAMO_TABLE_REQ_NAME"))
    tables = {
        "user": _DYNAMO_TABLE_USER,
        "lab": _DYNAMO_TABLE_LAB,
        "request": _DYNAMO_TABLE_REQ,
    }
    return _DYNAMO_CLIENT, _DYNAMO_DB, tables.get(table_id)


def _get_restricted_keys(table_id: str):
    return RESTRICTED_KEYS.get(table_id, [])


def _remove_restricted_keys(item: dict, table_id: str):
    for key in _get_restricted_keys(table_id):
        if key in item:
            del item[key]


def _key_dict_2_uniq_key(key_dict: dict) -> str:
    # Return a string representing all key names from a dict
    return "-".join([key_dict[k] for k in sorted(key_dict.keys())])


def _get_table_cache(table_id: str):
    return CACHES.get(table_id, {})


def is_cached(cache_key: str, table_id: str) -> bool:
    return cache_key in _get_table_cache(table_id)


def get_cache(cache_key: str, table_id: str) -> dict | None:
    if is_cached(cache_key, table_id):
        return _get_table_cache(table_id)[cache_key]
    return None


def _del_cache(cache_key: str, table_id: str) -> bool:
    if is_cached(cache_key, table_id):
        del _get_table_cache(table_id)[cache_key]
        return True
    return False


def _add_cache(key: dict, item: dict, table_id: str) -> dict:
    # Don't cache restricted keys, they are for internal use only.
    _remove_restricted_keys(item, table_id=table_id)
    cache_key = _key_dict_2_uniq_key(key)

    if table_id in CACHES:
        _get_table_cache(table_id)[cache_key] = item
    return item


def _check_cache_counter(key, table, table_id) -> bool:
    cache_value = get_cache(_key_dict_2_uniq_key(key), table_id)
    if "_rec_counter" not in cache_value:
        # User hasn't been updated since cache counter was added?
        return False
    if cache_value["_rec_counter"] != get_record_counter(table, key):
        return False
    return True


def alpha(s: str) -> str:
    """
    Only returns the alpha parts of a string.
    """
    return "".join(filter(str.isalnum, s))


def create_item(key: dict, item: dict, table_id: str) -> bool:
    """
    Creates an item in the DB.
    """
    _client, _db, table = _get_dynamo(table_id)
    # "Cast" to a plain dict, so it can be serialized to JSON.
    item = json.loads(json.dumps(item, default=str))
    for restricted_key in _get_restricted_keys(table_id):
        if restricted_key in item:
            raise ValueError(
                f"Can't set '{restricted_key}', that's one we set automatically and WILL get overridden."
            )
    item.update(key)
    item["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with measure_time(service="dynamo", action="put item"):
        table.put_item(Item=item)

    # Add new item to profile cache
    _add_cache(key, item, table_id)

    return True


def get_item(key: dict, table_id: str) -> dict:
    """
    Returns an item from the DB, or False if it doesn't exist.
    """
    _client, _db, table = _get_dynamo(table_id)
    # Check profile cache
    cache_key = _key_dict_2_uniq_key(key)
    if is_cached(cache_key, table_id):
        if _check_cache_counter(key, table, table_id):
            return get_cache(cache_key, table_id)

    with measure_time(service="dynamo", action="get item by username key"):
        response = table.get_item(Key=key)

    if "Item" in response:
        # Add response to cache & Return
        return _add_cache(key, response["Item"], table_id)
    return False


def get_record_counter(table, key) -> int:
    # no timing here, too much noise.
    response = table.get_item(
        Key=key,
        ProjectionExpression="#rec_counter",
        ExpressionAttributeNames={"#rec_counter": "_rec_counter"},
    )

    if "Item" not in response:
        # Item doesn't have a record yet
        return 1

    if "_rec_counter" not in response["Item"]:
        # Item doesn't have a counter yet
        return 1

    return int(response["Item"]["_rec_counter"])


def dynamo_filter(
    attr_name: str,
    filter_value: str | list | None = None,
    filter_action: str = "contains",
):
    if not filter_value or filter_action == "exists":
        return Attr(attr_name).exists()
    if filter_action == "contains":
        return Attr(attr_name).contains(filter_value)
    if filter_action == "in":
        return Attr(attr_name).is_in(filter_value)
    if filter_action == "eq":
        return Attr(attr_name).eq(filter_value)


def pull_all_pagination(table, limit, filterexpr=None):
    table_scan_params = {}

    if filterexpr:
        table_scan_params["FilterExpression"] = filterexpr

    with measure_time(service="dynamo", action="get all filtered user items"):
        response = table.scan(**table_scan_params)
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            table_scan_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = table.scan(**table_scan_params)
            items.extend(response.get("Items", []))

            # Break if we meet a set limit, and we're not filtering
            if limit and len(items) >= limit:
                break

    return items


def combine_all_dynamo_filters(filters):
    if not any(filters):
        return None

    # Local & all filters
    filters = [x for x in filters if x]
    filters_out = filters.pop(0)
    while len(filters):
        filters_out = filters_out & filters.pop(0)

    # all filters combined.
    return filters_out


def get_all_items(table_id: str, limit=None, filters=None) -> list:
    """
    Returns all items in the DB.
    Need to page because there's a 100 item limit.

    limit: A maximum list return length
    filters: Table filters

    """
    _client, _db, table = _get_dynamo(table_id)
    items = pull_all_pagination(table, limit, filters)
    logger.info(f"Fetched {len(items)} rows from {table} w/ filters={filters}")

    # Bound the return set if limit provided
    if limit:
        return items[:limit]

    return items


def update_item(key: dict, updates: dict, table_id: str) -> bool:
    """
    Updates fields in an existing item. (Will create fields if they don't exist.)

    updates: dict, each key-value pair is a different field that'll be updated. fields not
    listed will be left alone.
    """
    _client, _db, table = _get_dynamo(table_id)
    # "Cast" to a plain dict, so it can be serialized to JSON.
    updates = json.loads(json.dumps(updates, default=str))
    ### Fail fast if it doesn't exist, they should call create_item instead:
    if not get_item(key=key, table_id=table_id):
        return False

    ### Otherwise craft the boto3 update item call:
    updates["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ### increment the record counter
    updates["_rec_counter"] = get_record_counter(table, key) + 1

    # The '#var' is ID for the keys:
    expression_attribute_names = {f"#{alpha(k)}": k for k in updates.keys()}
    # The ':var' is ID for the values:
    expression_attribute_values = {f":{alpha(k)}": v for k, v in updates.items()}
    update_expression = "SET " + ", ".join(
        # Set the ID for #var and :var equal to each other:
        # (It'll look up the real value in the map above.)
        [f"#{alpha(k)}=:{alpha(k)}" for k in updates.keys()]
    )
    with measure_time(service="dynamo", action="update user item"):
        table.update_item(
            Key=key,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            UpdateExpression=update_expression,
        )

    # Profile was mutated, lets invalidate
    _del_cache(_key_dict_2_uniq_key(key), table_id)

    return True


def delete_item(key: dict, table_id: str) -> None:
    """
    Deletes an item from the DB & Cache.
    """
    _client, _db, table = _get_dynamo(table_id)
    _del_cache(_key_dict_2_uniq_key(key), table_id)
    with measure_time(service="dynamo", action="delete user item"):
        table.delete_item(Key=key)
