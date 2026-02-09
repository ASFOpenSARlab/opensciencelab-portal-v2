import os

from moto import mock_aws
import boto3

## This is here just to fix a weird import timing issue with importing utils directly
from util import dynamo_db as _  # noqa: F401 # pylint: disable=unused-import,import-error
from util.exceptions import UserNotFound
from util.user_ip_logs_stream import update_user_ip_in_db

import pytest

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
        assert get_all_items(table_id="user") == [], "DB should be empty at the start"

    def test_creating_user_updates_db(self):
        from objs.user.user import User
        from util.dynamo_db import get_all_items

        username = "test_user"
        email = "test_user@user.com"

        user = User(username)
        user.email = email
        assert len(get_all_items(table_id="user")) == 1, (
            "User was NOT inserted into the DB"
        )
        assert user.username == username, "Username attr doesn't match init"
        # Only one item, verify it's what we expect IN the DB too.
        assert get_all_items(table_id="user")[0]["access"] == ["user"], (
            "Access should be just 'user' by default"
        )
        assert get_all_items(table_id="user")[0]["email"] == email

    def test_username_immutable(self):
        from objs.user.user import User
        from util.exceptions import DbError

        # Username attr exists:
        username = "test_user"
        user = User(username)
        assert user.username == "test_user"

        # And you can't change it:
        with pytest.raises(DbError) as excinfo:
            user.username = "new_name"
        assert f"Key 'username' not in validator_map for user {user.username}" in str(
            excinfo.value
        )

    def test_class_method_is_default(self):
        # Test this early, so we can use it in future tests
        from objs.user.user import User

        username = "test_user"
        user = User(username)
        assert user.is_default("access", None) is False, "Access is not None"
        assert user.is_default("access", []) is False, "Access is not empty list"
        assert user.is_default("access", ["user"]) is True, (
            "Access defaults to just 'user'"
        )

    def test_defaults_applied(self):
        from objs.user.user import User
        from objs.user.validator_map import validator_map
        from objs.user.defaults import defaults
        from frozendict import deepfreeze

        username = "test_user"
        user = User(username)

        for attr in validator_map:
            if attr in defaults:
                # Deepfreeze modifies the value, so we need to compare it:
                assert getattr(user, attr) == deepfreeze(defaults[attr]), (
                    f"Default for '{attr}' should be applied"
                )
            else:
                assert getattr(user, attr) is None, (
                    f"User should have attribute '{attr}' set to None"
                )

    def test_cant_append_list_directly(self):
        from objs.user.user import User

        username = "test_user"
        user = User(username)

        # Access is a list, so it should be frozen:
        with pytest.raises(AttributeError) as excinfo:
            user.access.append("admin")
        assert "'tuple' object has no attribute 'append'" in str(excinfo.value)

    def test_can_modify_list_by_assignment(self):
        from objs.user.user import User
        from util.dynamo_db import get_all_items

        username = "test_user"
        user = User(username)

        # Access is a list, so we can modify it:
        assert list(user.access) == ["user"], "Base list is not just 'user'"
        assert not user.is_admin()
        user.access = list(user.access) + ["admin"]
        assert list(user.access) == ["user", "admin"], (
            "Access should now contain 'admin'"
        )
        assert user.is_admin()
        assert len(get_all_items(table_id="user")) == 1, (
            "There should still only be one item in the DB"
        )
        assert get_all_items(table_id="user")[0]["access"] == ["user", "admin"], (
            "Access should be updated in the DB too"
        )

    def test_limit_user_return(self):
        from objs.user.user import User
        from objs.user.user import user_email_filters
        from util.dynamo_db import get_all_items

        # Create some users to filter
        for i in range(10):
            username = f"test_user_{i}"
            User(username)
        for i in range(10):
            username = f"test_user_filter_{i}"
            User(username)

        assert len(get_all_items(table_id="user")) == 20, (
            "There should be 20 users in the DB"
        )
        assert len(get_all_items(table_id="user", limit=5)) == 5, (
            "There should be a limit of 5 users"
        )
        test_filter = user_email_filters(username_filter="filter", email_filter=None)
        assert len(get_all_items(table_id="user", filters=test_filter)) == 10, (
            "There should be 10 matched users"
        )
        assert len(get_all_items(table_id="user", limit=5, filters=test_filter)) == 5, (
            "There should be 5 matched and filtered users"
        )

    def test_get_users_with_lab(self, monkeypatch, helpers):
        from objs.user.user import User
        from objs.user import get_users_with_lab

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        user1 = User(username="test_user1")
        user1.labs = {"testlab": {}}

        user2 = User(username="test_user2")
        user2.labs = {"testlab": {}, "differentlab": {}}

        user3 = User(username="test_user3")
        user3.labs = {"differentlab": {}}

        output = get_users_with_lab("testlab")

        assert len(output) == 2
        assert output[0]["username"] == "test_user1"
        assert output[1]["username"] == "test_user2"

        assert len(get_users_with_lab("testlab", limit=2)) == 2, (
            "Limited results should be limited to 2"
        )
        assert len(get_users_with_lab("testlab", username_filter="test_user2")) == 1, (
            "Filtered results should be limited to 1"
        )
        assert (
            len(get_users_with_lab("testlab", username_filter="test_user", limit=2))
            == 2
        ), "Filtered and limited results should be limited to 2"

    def test_fetch_lab_requests(self, monkeypatch, helpers):
        from objs.lab.lab import Lab
        from objs.user.user import User

        LAB_CONFIGS = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("objs.lab.lab.LAB_CONFIGS", LAB_CONFIGS)

        testuser = "testuser"
        testlab = "testlab"

        # testlab exists as a fake lab
        lab = Lab(testlab)
        user = User(testuser)

        # should be no requests
        assert len(user.get_requests()) == 0

        # Add record
        lab.add_access_request(
            answers={
                "sar_experience": "I have no experience",
                "osl_experience": "I don't know what OSL is",
            },
            username=testuser,
        )

        # should now have a request
        assert len(user.get_requests()) == 1



    def test_delete_user(self, monkeypatch):
        from objs.user.user import User
        from util.dynamo_db import get_all_items

        # Don't try to actually delete the user from userpool
        monkeypatch.setattr(
            "objs.user.user.delete_user_from_user_pool", lambda *args, **kwargs: True
        )

        # Create user
        username = "test_user1"
        user1 = User(username=username)
        assert username in [x["username"] for x in get_all_items(table_id="user")]

        # Remove user
        user1.remove_user()
        assert username not in [x["username"] for x in get_all_items(table_id="user")]

    def test_user_profile_in_cache(self, monkeypatch):
        from objs.user.user import User
        from util.dynamo_db import is_cached

        monkeypatch.setattr(
            "objs.user.user.delete_user_from_user_pool", lambda *args, **kwargs: True
        )

        username = "test_user_cache1"
        assert not is_cached(username, "user")

        # Create a user
        _user_copy_0 = User(username=username)

        # Pull a user, this will be cached since it is not a create
        user_copy_1 = User(username=username)
        assert is_cached(username, "user")
        assert not user_copy_1.is_admin()

        # Mutate cache
        from util.dynamo_db import CACHES

        CACHES["user"][username]["access"].append("admin")

        # Fetch mutated profile to verify cache was used
        user_copy_2 = User(username=username)
        assert user_copy_2.is_admin()

        # Remove item from cache
        user_copy_1.remove_user()
        assert not is_cached(username, "user")

        # ensure cache record counter is increment
        user_copy_3 = User(username=username)
        uc3_counter_initial = user_copy_3._rec_counter
        user_copy_3.access = list(user_copy_3.access) + ["admin"]
        user_copy_4 = User(username=username)
        assert user_copy_4._rec_counter != uc3_counter_initial

    def test_user_create_if_missing_false(self):
        from objs.user.user import User

        with pytest.raises(UserNotFound) as exc_info:
            User(username="NotRealUser", create_if_missing=False)
        assert (
            exc_info.value.args[0]
            == "User NotRealUser does not exist and was not created"
        )

    def test_user_is_authorized_lab(self):
        from objs.user.user import User

        user = User(username="test_user")
        user.labs = {"testlab": {}}

        assert user.is_authorized_lab("testlab"), (
            "User should be authorized for testlab"
        )

        assert not user.is_authorized_lab("random-lab"), (
            "User should NOT be authorized for random-lab"
        )

    def test_user_is_authorized_lab_admin(self):
        from objs.user.user import User

        user = User(username="test_user")
        user.access = list(user.access) + ["admin"]

        assert user.is_authorized_lab("testlab"), (
            "Admin should be authorized for testlab"
        )

    def test_user_update_ip_address(self):
        from objs.user.user import User

        message = {
            "username": "test_user",
            "ip_address": "0.0.0.0",
            "country_code": "ZZ",
        }

        user1 = User(username=message["username"])

        assert user1.ip_address is None
        assert user1.country_code is None

        update_user_ip_in_db(**message)

        user2 = User(username=message["username"])

        assert user2.ip_address == "0.0.0.0"
        assert user2.country_code == "ZZ"
