import os

from moto import mock_aws
import boto3
import pytest

# ## This is here just to fix a weird import timing issue with importing utils directly
# from util.user import dynamo_db as _  # noqa: F401 # pylint: disable=unused-import,import-error

REGION = os.getenv("STACK_REGION", "us-west-2")

@mock_aws
class TestUserClass:
    def setup_class():
        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util

        util.user.dynamo_db._DYNAMO_CLIENT = boto3.client(
            "dynamodb",
            region_name=REGION,
        )
        util.user.dynamo_db._DYNAMO_DB = boto3.resource(
            "dynamodb",
            region_name=REGION,
        )

    def setup_method(self, method):
        from util.user.dynamo_db import get_all_items

        ## These imports have to be the long forum, to let us modify the values here:
        # https://stackoverflow.com/a/12496239/11650472
        import util

        user_table_name = "TestUserTable"
        util.user.dynamo_db._DYNAMO_DB.create_table(
            TableName=user_table_name,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "username", "AttributeType": "S"}],
        )
        ## No need to delete the table between methods, it goes out of scope anyways.
        util.user.dynamo_db._DYNAMO_TABLE = util.user.dynamo_db._DYNAMO_DB.Table(
            user_table_name
        )
        assert get_all_items() == [], "DB should be empty at the start"

    def test_creating_user_updates_db(self):
        from util.user.user import User
        from util.user.dynamo_db import get_all_items

        username = "test_user"
        user = User(username)
        assert len(get_all_items()) == 1, "User was NOT inserted into the DB"
        assert user.username == username, "Username attr doesn't match init"
        # Only one item, verify it's what we expect IN the DB too.
        assert get_all_items()[0]["access"] == ["user"], (
            "Access should be just 'user' by default"
        )

    def test_username_immutable(self):
        from util.user.user import User
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
        from util.user.user import User

        username = "test_user"
        user = User(username)
        assert user.is_default("access", None) is False, "Access is not None"
        assert user.is_default("access", []) is False, "Access is not empty list"
        assert user.is_default("access", ["user"]) is True, (
            "Access defaults to just 'user'"
        )

    def test_defaults_applied(self):
        from util.user.user import User
        from util.user.validator_map import validator_map
        from util.user.defaults import defaults
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
        from util.user.user import User

        username = "test_user"
        user = User(username)

        # Access is a list, so it should be frozen:
        with pytest.raises(AttributeError) as excinfo:
            user.access.append("admin")
        assert "'tuple' object has no attribute 'append'" in str(excinfo.value)

    def test_can_modify_list_by_assignment(self):
        from util.user.user import User
        from util.user.dynamo_db import get_all_items

        username = "test_user"
        user = User(username)

        # Access is a list, so we can modify it:
        assert list(user.access) == ["user"], "Base list is not just 'user'"
        user.access = list(user.access) + ["admin"]
        assert list(user.access) == ["user", "admin"], (
            "Access should now contain 'admin'"
        )
        assert len(get_all_items()) == 1, (
            "There should still only be one item in the DB"
        )
        assert get_all_items()[0]["access"] == ["user", "admin"], (
            "Access should be updated in the DB too"
        )

