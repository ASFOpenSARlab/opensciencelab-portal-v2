import os
from datetime import datetime

from moto import mock_aws
import boto3

import pytest

## This is here just to fix a weird import timing issue with importing utils directly
from util import dynamo_db as _  # noqa: F401 # pylint: disable=unused-import,import-error
from util.exceptions import LabDoesNotExist, InvalidLabRequestStatus

REGION = os.getenv("STACK_REGION", "us-west-2")


@mock_aws
class TestLabClass:
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

    def test_endpoint_add_token(
        self, monkeypatch, lambda_context, helpers, fake_auth, mocker
    ):
        import main

        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        mock_add_token = mocker.patch("objs.lab.lab.Lab.create_access_token")
        mock_remove_token = mocker.patch("objs.lab.lab.Lab.remove_access_token")

        # Adding token
        bodystr = {
            "action": "add_token",
            "lab_profiles": "m6a.large",
            "start_date": "2026-03-31",
            "end_date": "",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab/edittokens",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )
        main.lambda_handler(event, lambda_context)

        # Assert correct function is called with correct parameters
        mock_add_token.assert_called_once_with(
            start_date=datetime.strptime("2026-03-31", "%Y-%m-%d"),
            end_date=None,
            profiles=["m6a.large"],
        )
        assert mock_remove_token.call_count == 0

    def test_endpoint_add_token_invalid_dates(
        self, monkeypatch, lambda_context, helpers, fake_auth, mocker
    ):
        import main

        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        mock_add_token = mocker.patch("objs.lab.lab.Lab.create_access_token")
        mock_remove_token = mocker.patch("objs.lab.lab.Lab.remove_access_token")

        # Adding token
        bodystr = {
            "action": "add_token",
            "lab_profiles": "m6a.large",
            "start_date": "2026-03-31",
            "end_date": "2026-03-10",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab/edittokens",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )
        ret = main.lambda_handler(event, lambda_context)

        # Assert no adding tokens and redirect
        assert mock_add_token.call_count == 0
        assert mock_remove_token.call_count == 0
        assert (
            ret["headers"].get("Location") == "/portal/access/manage/testlab/edittokens"
        )

    def test_endpoint_remove_token(
        self, monkeypatch, lambda_context, helpers, fake_auth, mocker
    ):
        import main

        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        mock_add_token = mocker.patch("objs.lab.lab.Lab.create_access_token")
        mock_remove_token = mocker.patch("objs.lab.lab.Lab.remove_access_token")

        # Removing token
        bodystr = {
            "action": "remove_token",
            "token": "309308e2-20c7",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab/edittokens",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )
        main.lambda_handler(event, lambda_context)

        # Assert correct function is called with correct parameters
        assert mock_add_token.call_count == 0
        mock_remove_token.assert_called_once_with("309308e2-20c7")

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
        lab1.set_access_request_status(
            username=username, status="rejected", reviewer="adminuser"
        )
        current_request = lab1.get_access_request(username)
        assert current_request.get("status") == "rejected"

        # Reject updates to "finalized requests"
        with pytest.raises(InvalidLabRequestStatus) as excinfo:
            lab1.set_access_request_status(
                username=username, status="approved", reviewer="adminuser"
            )
        assert "Attempt to update request in status" in str(excinfo.value)

        # Reject invalid statue
        with pytest.raises(InvalidLabRequestStatus) as excinfo:
            lab1.set_access_request_status(
                username="different_user", status="free", reviewer="adminuser"
            )
        assert "Status 'free' not in" in str(excinfo.value)

        # Catch updates to request that doesn't exist
        with pytest.raises(InvalidLabRequestStatus) as excinfo:
            lab1.set_access_request_status(
                username="joe-bob", status="pending", reviewer="adminuser"
            )
        assert "has not requested access to" in str(excinfo.value)

    def test_resubmitted_lab_request(self, helpers, monkeypatch):
        from objs.lab.lab import Lab

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        username = "testuser"

        # testlab exists as a fake lab
        lab1 = Lab("testlab")

        # Add insufficient request
        lab1.add_access_request(
            answers={
                "sar_experience": "I have no experience",
                "osl_experience": "I don't know what OSL is",
            },
            username=username,
        )

        # Return request
        lab1.set_access_request_status(
            username=username,
            status="returned",
            reviewer="adminuser",
            reviewer_comment="Returned for more info",
        )

        # Verify the request is returned
        current_request = lab1.get_access_request(username)
        assert current_request["status"] == "returned"

        # Add a better response
        lab1.add_access_request(
            answers={
                "sar_experience": "I have lots experience",
                "osl_experience": "I've used OSL before",
            },
            username=username,
        )

        # Verify the status is returned to "new"
        current_request = lab1.get_access_request(username)
        assert current_request["status"] == "new"

        # Force lab to "imported"
        current_request["status"] = "imported"
        lab1._put_access_request(current_request, username)
        imported_request = lab1.get_access_request(username)
        assert imported_request["status"] == "imported"

        # Update imported
        lab1.add_access_request(
            answers={
                "sar_experience": "I requested long ago",
                "osl_experience": "Please let me back in",
            },
            username=username,
        )

        # Verify imported has become "new" again
        post_imported_request = lab1.get_access_request(username)
        assert post_imported_request["status"] == "new"

    def test_successful_req_approval(self, helpers, monkeypatch):
        from objs.lab.lab import Lab
        from objs.user.user import User
        from util.access_request import request_status_change_action

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)
        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", LAB_CONFIGS)
        monkeypatch.setattr("util.access_request.LAB_CONFIGS", LAB_CONFIGS)
        monkeypatch.setattr(
            "util.access_request.send_user_email",
            lambda *args, **kwargs: ("Success", "Email Sent"),
        )

        username = "testuser"
        labname = "testlab"

        # Create user w/o access
        user = User(username)

        # Validate user DOES NOT have access
        assert not user.is_authorized_lab(labname)

        # Add access
        lab = Lab(labname)
        lab.add_access_request(
            answers={
                "sar_experience": "I have lots experience",
                "osl_experience": "I've used OSL before",
            },
            username=username,
        )

        # Approve user
        request_status_change_action(lab, username, "approved")
        lab.set_access_request_status(
            username=username,
            status="approved",
            reviewer="AdminUser",
            reviewer_comment="Approved for Testing",
        )

        # Find request
        access_request = lab.get_access_request(username)
        assert access_request.get("status") == "approved"

        # Re-fetch user because of internal caching
        user2 = User(username)

        # Validate user access
        assert user2.is_authorized_lab(labname)

    def test_fetch_lab_requests(self, helpers, monkeypatch):
        from objs.lab.lab import Lab
        from util.dynamo_db import dynamo_filter, get_all_items

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

        lab2.set_access_request_status(
            username=username2,
            status="rejected",
            reviewer="adminuser",
            reviewer_comment="Abusive User",
        )

        # Make sure we get back only lab1
        lab1_request = lab1.get_requests()
        assert len(lab1_request) == 1

        # Make sure we get back only lab2
        lab2_request = lab2.get_requests(status=["new", "pending"])
        assert len(lab2_request) == 1

        # Make sure the reviewers name & comment are present
        rej_request = lab2.get_requests(status=["rejected"])
        assert rej_request[0]["answers"][-1]["submission_comment"] == "Abusive User"
        assert rej_request[0]["answers"][-1]["submission_reviewer"] == "adminuser"

        # Filter username has the string "user"
        filters_contains = dynamo_filter(
            attr_name="username", filter_value="user", filter_action="contains"
        )
        assert (
            len(get_all_items(table_id="request", limit=200, filters=filters_contains))
            == 3
        )

        # Filter username has the string "user"
        filters_is = dynamo_filter(
            attr_name="username", filter_value="testuser", filter_action="eq"
        )
        assert (
            len(get_all_items(table_id="request", limit=200, filters=filters_is)) == 1
        )

    def test_country_restrictions(self, helpers, monkeypatch):
        from objs.base_lab_config import get_daac_country_status

        restrictions = get_daac_country_status()

        assert "prohibited" in restrictions
        assert "limited" in restrictions
        assert "US" not in restrictions["prohibited"]
        assert "US" not in restrictions["limited"]
        assert "IR" in restrictions["prohibited"]
        assert "IR" not in restrictions["limited"]
        assert "IL" in restrictions["limited"]
        assert "IL" not in restrictions["prohibited"]

    def test_get_access_tokens(self, helpers, monkeypatch):
        from objs.lab.lab import Lab

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        lab_no_token = Lab("protectedlab")
        lab_with_token = Lab("testlab")

        assert not lab_no_token.create_access_token()
        assert lab_with_token.create_access_token()

        # Make sure we have a token
        one_token = lab_with_token.get_valid_access_tokens()
        assert len(one_token) == 1
        one_token_string_value = list(one_token[0])[0]
        assert one_token_string_value
        # Make sure we get the default profiles
        assert set(one_token[0][one_token_string_value]) == {"m6a.large", "m6a.xlarge"}

        # Create expired token
        lab_with_token.create_access_token(
            end_date=datetime.strptime("2020-10-01", "%Y-%m-%d")
        )

        # should only return 1 token
        assert len(lab_with_token.get_valid_access_tokens()) == 1

        # Make sure we can get a non-default set of profiles
        lab_with_token.create_access_token(profiles=["m6a.large"])
        assert len(lab_with_token.get_valid_access_tokens()) == 2
        for valid_token in lab_with_token.get_valid_access_tokens():
            if one_token_string_value not in valid_token:
                # this is the single profile token
                token_value = list(valid_token)[0]
                assert set(valid_token[token_value]) == {"m6a.large"}

    def test_process_access_tokens(self, helpers, monkeypatch):
        from objs.lab.lab import Lab
        from util.access_request import process_access_token

        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.access_request.User", lambda *args, **kwargs: user)

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)
        monkeypatch.setattr("util.access_request.LAB_CONFIGS", LAB_CONFIGS)

        lab_with_token = Lab("testlab")
        assert lab_with_token.create_access_token()
        token = list(lab_with_token.get_valid_access_tokens()[0])[0]

        assert process_access_token(token, "test_user")

    def test_remove_access_token(self, helpers, monkeypatch):
        from objs.lab.lab import Lab

        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.access_request.User", lambda *args, **kwargs: user)

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)
        monkeypatch.setattr("util.access_request.LAB_CONFIGS", LAB_CONFIGS)

        # Create lab with target token
        lab_with_token = Lab("testlab")
        lab_with_token.create_access_token()
        lab_with_token.create_access_token()
        lab_with_token.create_access_token()
        token_values = [
            list(token.keys())[0] for token in lab_with_token.get_valid_access_tokens()
        ]
        target_token_value = token_values[0]
        remaining_token_values = token_values[1:]

        # Function returns true
        assert lab_with_token.remove_access_token(target_token_value)

        all_token_values_post_remove = [
            list(token.keys())[0] for token in lab_with_token.get_valid_access_tokens()
        ]
        # Target token removed
        assert target_token_value not in all_token_values_post_remove
        # All other tokens are still present
        assert all(
            [
                token_value in all_token_values_post_remove
                for token_value in remaining_token_values
            ]
        )
