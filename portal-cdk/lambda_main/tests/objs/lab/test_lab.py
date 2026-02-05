import os

from moto import mock_aws
import boto3

import pytest

## This is here just to fix a weird import timing issue with importing utils directly
from util import dynamo_db as _  # noqa: F401 # pylint: disable=unused-import,import-error
from util.exceptions import LabDoesNotExist

REGION = os.getenv("STACK_REGION", "us-west-2")


@mock_aws
class TestUserClass:
    def setup_class():
        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util

        util.dynamo_db._DYNAMO_CLIENT = boto3.client(
            "dynamodb",
            region_name=REGION,
        )
        util.dynamo_db._DYNAMO_DB = boto3.resource(
            "dynamodb",
            region_name=REGION,
        )

    def setup_method(self, method):
        from util.dynamo_db import get_all_items

        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util

        user_table_name = "TestUserTable"
        lab_table_name = "TestLabTable"
        util.dynamo_db._DYNAMO_DB.create_table(
            TableName=user_table_name,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "username", "AttributeType": "S"}],
        )
        util.dynamo_db._DYNAMO_DB.create_table(
            TableName=lab_table_name,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "labname", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "labname", "AttributeType": "S"}],
        )
        ## No need to delete the table between methods, it goes out of scope anyways.
        util.dynamo_db._DYNAMO_TABLE_USER = util.dynamo_db._DYNAMO_DB.Table(
            user_table_name
        )
        util.dynamo_db._DYNAMO_TABLE_LAB = util.dynamo_db._DYNAMO_DB.Table(
            lab_table_name
        )
        assert get_all_items(table_name="lab") == [], "DB should be empty at the start"

    def test_load_lab_creates_db_row(self, helpers, monkeypatch):
        from objs.lab.lab import Lab
        from util.dynamo_db import get_all_items

        LABS = helpers.FAKE_LABS
        # monkeypatch.setattr("portal.access.LABS", LABS)
        monkeypatch.setattr("objs.lab.lab.LABS", LABS)

        # testlab exists as a fake lab
        lab1 = Lab("testlab")
        assert not lab1.allow_request_access, (
            "Lab allow_request_access does not match default"
        )
        assert len(get_all_items(table_name="lab")) == 1, (
            "Lab was NOT inserted into the DB"
        )

        # doesnotexist is not a valid fake lab
        with pytest.raises(LabDoesNotExist) as excinfo:
            _lab2 = Lab("doesnotexist")
        assert "Lab doesnotexist does not exist." in str(excinfo.value)

        assert "doesnotexist" not in get_all_items(table_name="lab"), (
            "invalid lab doesnotexist mistakenly added to Labs table"
        )

        lab1.allow_request_access = True

        lab3 = Lab("testlab")
        assert lab3.allow_request_access, (
            "Lab allow_request_access was not updated in DB"
        )
