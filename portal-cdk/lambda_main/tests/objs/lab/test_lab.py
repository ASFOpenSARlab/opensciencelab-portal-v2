import os

from moto import mock_aws
import boto3

import pytest

## This is here just to fix a weird import timing issue with importing utils directly
from util import dynamo_db as _  # noqa: F401 # pylint: disable=unused-import,import-error
from util.exceptions import LabDoesNotExist, InvalidLabRequestStatus

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
        req_table_name = "TestRequestsTable"
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
        util.dynamo_db._DYNAMO_DB.create_table(
            TableName=req_table_name,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "labname", "KeyType": "HASH"},
                {"AttributeName": "username", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "labname", "AttributeType": "S"},
                {"AttributeName": "username", "AttributeType": "S"},
            ],
        )
        ## No need to delete the table between methods, it goes out of scope anyways.
        util.dynamo_db._DYNAMO_TABLE_USER = util.dynamo_db._DYNAMO_DB.Table(
            user_table_name
        )
        util.dynamo_db._DYNAMO_TABLE_LAB = util.dynamo_db._DYNAMO_DB.Table(
            lab_table_name
        )
        util.dynamo_db._DYNAMO_TABLE_REQ = util.dynamo_db._DYNAMO_DB.Table(
            req_table_name
        )

        assert get_all_items(table_id="lab") == [], "DB should be empty at the start"

    def test_load_lab_creates_db_row(self, helpers, monkeypatch):
        from objs.lab.lab import Lab
        from util.dynamo_db import get_all_items

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        # testlab exists as a fake lab
        lab1 = Lab("testlab")
        assert not lab1.allow_request_access, (
            "Lab allow_request_access does not match default"
        )
        assert len(get_all_items(table_id="lab")) == 1, (
            "Lab was NOT inserted into the DB"
        )

        # doesnotexist is not a valid fake lab
        with pytest.raises(LabDoesNotExist) as excinfo:
            _lab2 = Lab("doesnotexist")
        assert "Lab doesnotexist does not exist." in str(excinfo.value)

        assert "doesnotexist" not in get_all_items(table_id="lab"), (
            "invalid lab doesnotexist mistakenly added to Labs table"
        )

        lab1.allow_request_access = True

        lab3 = Lab("testlab")
        assert lab3.allow_request_access, (
            "Lab allow_request_access was not updated in DB"
        )

    def test_load_lab_requests(self, helpers, monkeypatch):
        from objs.lab.lab import Lab
        from util.dynamo_db import get_all_items

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)
        username = "testuser"

        # testlab exists as a fake lab
        lab1 = Lab("testlab")

        # Add record
        lab1.add_access_request(
            answers={
                "sar_experience": "I have no experience",
                "osl_experience": "I don't know what OSL is",
            },
            username=username,
        )

        # request is now is status "new"
        current_request = lab1.get_access_request(username)
        assert current_request.get("status") == "new"

        # Supplied and unsupplied parameters exist
        assert current_request["answers"][0]["sar_experience"]
        assert not current_request["answers"][0]["use_case"]

        # make sure we have 1 record.
        all_request = get_all_items("request")
        assert len(all_request) == 1

        lab1.add_access_request(
            answers={
                "sar_experience": "I have no experience",
                "osl_experience": "I don't know what OSL is",
                "use_case": "I may or may not mine crypto",
            },
            username=username,
        )

        # make sure we STILL have 1 record.
        all_request = get_all_items("request")
        assert len(all_request) == 1

        # there should now be TWO answer dicts
        current_request = lab1.get_access_request(username)
        assert len(current_request["answers"]) == 2

        lab1.add_access_request(
            answers={
                "sar_experience": "SAR Expert",
                "osl_experience": "I'm an OSL Developer",
                "use_case": "Pro-level OSL Development",
            },
            username="different_user",
        )

        # make sure we now have 2 records
        all_request = get_all_items("request")
        assert len(all_request) == 2

        # Make sure we can change the Status
        lab1.set_access_request_status(username=username, status="rejected")
        current_request = lab1.get_access_request(username)
        assert current_request.get("status") == "rejected"

        # Reject updates to "finalized requests"
        with pytest.raises(InvalidLabRequestStatus) as excinfo:
            lab1.set_access_request_status(username=username, status="approved")
        assert "Attempt to update request in status" in str(excinfo.value)

        # Reject invalid statue
        with pytest.raises(InvalidLabRequestStatus) as excinfo:
            lab1.set_access_request_status(username="different_user", status="free")
        assert "Status 'free' not in" in str(excinfo.value)

        # Catch updates to request that doesn't exist
        with pytest.raises(InvalidLabRequestStatus) as excinfo:
            lab1.set_access_request_status(username="joe-bob", status="pending")
        assert "has not requested access to" in str(excinfo.value)

    def test_fetch_lab_requests(self, helpers, monkeypatch):
        from objs.lab.lab import Lab

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        username1 = "testuser"
        username2 = "rejectuser"

        # testlab exists as a fake lab
        lab1 = Lab("testlab")
        lab2 = Lab("protectedlab")

        # Add record
        lab1.add_access_request(
            answers={
                "sar_experience": "I have no experience",
                "osl_experience": "I don't know what OSL is",
            },
            username=username2,
        )

        lab2.add_access_request(
            answers={
                "sar_experience": "SAR Expert",
                "osl_experience": "I'm an OSL Developer",
                "use_case": "Pro-level OSL Development",
            },
            username=username1,
        )

        lab2.add_access_request(
            answers={
                "sar_experience": "Bad Request",
                "osl_experience": "Zero",
                "use_case": "Pro-level OSL Development",
            },
            username=username2,
        )

        lab2.set_access_request_status(username=username2, status="rejected")

        # Make sure we get back only lab1
        lab1_request = lab1.get_requests()
        assert len(lab1_request) == 1

        # Make sure we get back only lab2
        lab2_request = lab2.get_requests(status=["new", "pending"])
        assert len(lab2_request) == 1