"""File of helpers for interacting with DynamoDB."""
import datetime
import os

import boto3


_DYNAMO_CLIENT = None
_DYNAMO_DB = None
_DYNAMO_TABLE = None


def _get_dynamo():
    """
    Lazy load all DynamoDB stuff since it takes forever the first time.
    """
    global _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE # pylint: disable=global-statement
    if not _DYNAMO_CLIENT:
        _DYNAMO_CLIENT = boto3.client('dynamodb')
    if not _DYNAMO_DB:
        _DYNAMO_DB = boto3.resource("dynamodb")
    if not _DYNAMO_TABLE:
        _DYNAMO_TABLE = _DYNAMO_DB.Table(os.getenv('DYNAMO_TABLE_NAME'))
    return _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE


def alpha(s: str) -> str:
    """
    Only returns the alpha parts of a string.
    """
    return ''.join(filter(str.isalnum, s))


def create_item(username: str, item: dict) -> dict:
    """
    Creates an item in the DB.
    """
    _client, _db, table = _get_dynamo()
    # Adding ID here so you don't have to remember what the key should be, and
    # it matches the parameters for the other functions in this file.
    item['id'] = username
    item['created-at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item['last-update'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table.put_item(Item=item)
    return item


def get_item(username: str) -> dict:
    """
    Returns an item from the DB, or False if it doesn't exist.
    """
    _client, _db, table = _get_dynamo()
    response = table.get_item(Key={'id': username})
    if 'Item' in response:
        return response['Item']
    return False


def get_all_items() -> list:
    """
    Returns all items in the DB.
    Need to page because there's a 100 item limit.
    """
    _client, _db, table = _get_dynamo()
    response = table.scan()
    items = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    return items


def update_item(username: str, updates: dict) -> dict:
    """
    Updates fields in an existing item. (Will create fields if they don't exist.)

    updates: dict, each key-value pair is a different field that'll be updated. fields not
    listed will be left alone.
    """
    _client, _db, table = _get_dynamo()
    ### If it doesn't exist, use the create_item function instead since that might
    # add extra fields, like when the item was created:
    if not get_item(username):
        return create_item(username, updates)
    ### Otherwise craft the boto3 update item call:
    updates['last-update'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expression_attribute_names = {f"#{alpha(k)}": k for k in updates.keys()}
    expression_attribute_values = {f":{alpha(k)}": v for k, v in updates.items()}
    update_expression = "SET " + ", ".join([f"#{alpha(k)}=:{alpha(k)}" for k in updates.keys()])
    table.update_item(
        Key={'id': username},
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        UpdateExpression=update_expression,
    )
    return get_item(username)


def delete_item(username: str) -> None:
    """
    Deletes an item from the DB.
    """
    _client, _db, table = _get_dynamo()
    table.delete_item(Key={'id': username})


def update_username(old_username: str, new_username: str) -> bool:
    """
    Updates the username of an item in the DB.
    Since it's the primary key, you can't update it directly.
    Returns Bool: if old_username existed in DB already.
    """
    _client, _db, table = _get_dynamo()
    item = get_item(old_username)
    if item:
        item['id'] = new_username
        table.put_item(Item=item)
        delete_item(old_username)
        return True
    return False
