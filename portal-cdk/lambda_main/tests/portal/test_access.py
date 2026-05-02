from datetime import datetime
import json
import os

import boto3
from moto import mock_aws

import main
from util.exceptions import UserNotFound
from data import DATE_F


@mock_aws
class TestAccessPages:
    def test_user_accessing_manage_page(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(
            path="/portal/access/manage/testlab", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert "User does not have required access" in ret["body"]
        assert ret["headers"].get("Location") == "/portal"
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_admin_accessing_manage_page(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        # Checks permission required to access page
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        labs = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("portal.access.LAB_CONFIGS", labs)
        monkeypatch.setattr(
            "portal.access.Lab", lambda *args, **kwargs: helpers.FakeLab()
        )

        def lab_users_static(*args, **kwargs):
            return [
                {
                    "username": "test_user",
                    "email": "test@user.com",
                    "labs": {
                        "testlab": {
                            "lab_profiles": ["m6a.large"],
                        },
                    },
                    "token_usage": [
                        {
                            "labname": "testlab",
                            "token": "token-dne",
                            "apply_date": datetime.now().strftime(DATE_F),
                        }
                    ],
                }
            ]

        monkeypatch.setattr("portal.access.get_users_with_lab", lab_users_static)

        event = helpers.get_event(
            path="/portal/access/manage/testlab", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Test Lab") > -1
        # Add/refactor more asserts after manage page layout is figured out more
        assert (
            ret["body"].find(
                '<button type="submit" name="action" value="add_user">Add</button>'
            )
            > -1
        )
        assert (
            ret["body"].find(
                """onclick="fillRemoveUserForm('testlab', 'test_user');">Remove</button>"""
            )
            > -1
        )
        assert ret["body"].find('value="m6a.large, m6a.xlarge"')
        assert ret["headers"].get("Content-Type") == "text/html"
        assert ret["body"].find("token-dne")
        assert ret["body"].find("test@user.com")

        # Make sure tokens don't show up on lab w/o tokens
        event = helpers.get_event(
            path="/portal/access/manage/protectedlab", cookies=fake_auth
        )
        ret2 = main.lambda_handler(event, lambda_context)
        assert ret2["body"].find("Token") == -1

    def test_lab_manager_accessing_allowed_manage_page(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        # Checks permission required to access page
        user = helpers.FakeUser(access=["user", "lab_manager"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        labs = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("portal.access.LAB_CONFIGS", labs)
        lab = helpers.FakeLab(managers=[user.username])
        monkeypatch.setattr(
            "portal.access.Lab",
            lambda *args, **kwargs: lab,
        )
        monkeypatch.setattr("util.auth.Lab", lambda *args, **kwargs: lab)

        def lab_users_static(*args, **kwargs):
            return [
                {
                    "username": "test_user",
                    "email": "test@user.com",
                    "labs": {
                        "testlab": {
                            "lab_profiles": ["m6a.large"],
                        },
                    },
                    "token_usage": [
                        {
                            "labname": "testlab",
                            "token": "token-dne",
                            "apply_date": datetime.now().strftime(DATE_F),
                        }
                    ],
                }
            ]

        monkeypatch.setattr("portal.access.get_users_with_lab", lab_users_static)

        event = helpers.get_event(
            path="/portal/access/manage/testlab", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Test Lab") > -1
        # Add/refactor more asserts after manage page layout is figured out more
        assert (
            ret["body"].find(
                '<button type="submit" name="action" value="add_user">Add</button>'
            )
            > -1
        )
        assert (
            ret["body"].find(
                """onclick="fillRemoveUserForm('testlab', 'test_user');">Remove</button>"""
            )
            > -1
        )
        assert ret["body"].find('value="m6a.large, m6a.xlarge"')
        assert ret["headers"].get("Content-Type") == "text/html"
        assert ret["body"].find("token-dne")

        # Make sure tokens don't show up on lab w/o tokens
        event = helpers.get_event(
            path="/portal/access/manage/protectedlab", cookies=fake_auth
        )
        ret2 = main.lambda_handler(event, lambda_context)
        assert ret2["body"].find("Token") == -1
        assert ret["body"].find("test@user.com")

    def test_lab_manager_accessing_restricted_manage_page(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        # Checks permission required to access page
        user = helpers.FakeUser(access=["user", "lab_manager"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        labs = helpers.FAKE_LAB_CONFIGS
        monkeypatch.setattr("portal.access.LAB_CONFIGS", labs)
        monkeypatch.setattr(
            "portal.access.Lab", lambda *args, **kwargs: helpers.FakeLab()
        )

        lab = helpers.FakeLab()
        monkeypatch.setattr("util.auth.Lab", lambda *args, **kwargs: lab)

        def lab_users_static(*args, **kwargs):
            return [
                {
                    "username": "test_user",
                    "labs": {
                        "testlab": {
                            "lab_profiles": ["m6a.large"],
                        },
                    },
                    "token_usage": [
                        {
                            "labname": "testlab",
                            "token": "token-dne",
                            "apply_date": datetime.now().strftime(DATE_F),
                        }
                    ],
                }
            ]

        monkeypatch.setattr("portal.access.get_users_with_lab", lab_users_static)

        event = helpers.get_event(
            path="/portal/access/manage/testlab", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "Redirecting to Portal"
        assert ret["headers"].get("Location") == "/portal"

    def test_admin_edit_user_add_lab(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        lab = helpers.FakeLab(access_requests=None)
        monkeypatch.setattr("portal.access.Lab", lambda *args, **kwargs: lab)

        # Adding lab
        bodystr = {
            "username": "test_user",
            "lab_profiles": "",
            "action": "add_user",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab2/edituser",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert "testlab2" in user.labs
        assert user.labs["testlab2"] == {
            "lab_profiles": [""],
        }

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal/access/manage/testlab2"
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_admin_edit_user_remove_lab(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        lab = helpers.FakeLab(access_requests=None)
        monkeypatch.setattr("portal.access.Lab", lambda *args, **kwargs: lab)
        # Remove user
        bodystr = {
            "username": "test_user",
            "action": "remove_user",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab2/edituser",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert "testlab2" not in user.labs

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal/access/manage/testlab2"
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_admin_edit_user_invalid_action(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        lab = helpers.FakeLab(access_requests=None)
        monkeypatch.setattr("portal.access.Lab", lambda *args, **kwargs: lab)
        # Invalid action
        bodystr = {
            "username": "test_user",
            "action": "steal_the_moon",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab2/edituser",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 400
        assert "Invalid action" in ret["body"]

    def test_lab_manager_edit_user_has_permission(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "lab_manager"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        lab = helpers.FakeLab(access_requests=None, managers=["test_user"])
        monkeypatch.setattr("portal.access.Lab", lambda *args, **kwargs: lab)
        monkeypatch.setattr("util.auth.Lab", lambda *args, **kwargs: lab)
        # Add User
        bodystr = {
            "username": "test_user",
            "lab_profiles": "",
            "action": "add_user",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab2/edituser",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )

        ret = main.lambda_handler(event, lambda_context)

        assert "testlab2" in user.labs
        assert user.labs["testlab2"] == {
            "lab_profiles": [""],
        }

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal/access/manage/testlab2"
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_lab_manager_edit_user_missing_permission(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "lab_manager"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        lab = helpers.FakeLab(access_requests=None)
        monkeypatch.setattr("portal.access.Lab", lambda *args, **kwargs: lab)
        monkeypatch.setattr("util.auth.Lab", lambda *args, **kwargs: lab)
        # Add User
        bodystr = {
            "username": "test_user",
            "lab_profiles": "",
            "action": "add_user",
        }
        monkeypatch.setattr(
            "portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr
        )

        event = helpers.get_event(
            path="/portal/access/manage/testlab2/edituser",
            cookies=fake_auth,
            body="placeholder",
            method="POST",
        )

        ret = main.lambda_handler(event, lambda_context)

        assert "testlab2" not in user.labs

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal"
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_get_labs_of_a_user_admin_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        event = helpers.get_event(
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        response_body = json.loads(ret["body"])
        lab_access = response_body.get("labs")

        assert ret["statusCode"] == 200
        assert lab_access["viewable_labs_config"].get("testlab")
        assert lab_access["viewable_labs_config"].get("differentlab")
        assert lab_access["viewable_labs_config"].get("noaccess")
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_get_labs_of_a_user_not_admin_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"], username="test_admin")
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        targetuser = helpers.FakeUser(
            access=["user"],
            username="test_user2",
            labs={
                "testlab": {
                    "lab_profiles": None,
                },
            },
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        event = helpers.get_event(
            path="/portal/access/labs/test_user2",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        response_body = json.loads(ret["body"])
        lab_access = response_body.get("labs")

        assert ret["statusCode"] == 200
        assert lab_access["viewable_labs_config"].get("testlab")
        assert lab_access["viewable_labs_config"].get("differentlab")
        assert not lab_access["viewable_labs_config"].get("noaccess")
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_lab_access_of_user(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(access=["user", "admin"], username="test_admin")
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        targetuser = helpers.FakeUser(
            access=["user"],
            username="test_user2",
            labs={
                "testlab": {
                    "lab_profiles": None,
                },
                # protectedlab is deliberately not here, it should be marked as able to see but not access
                # noaccess is deliberately not here, should not be present
            },
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        event = helpers.get_event(
            path="/portal/access/labs/test_user2",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        response_body = json.loads(ret["body"])
        lab_access = response_body.get("labs")

        assert lab_access["lab_access"]["testlab"]["can_user_access_lab"]
        assert "testlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"]["protectedlab"]["can_user_access_lab"]
        assert "protectedlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"].get("noaccess")
        assert "noaccess" not in lab_access["viewable_labs_config"]

    def test_lab_access_of_admin(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(access=["user", "admin"], username="test_admin")
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        targetuser = helpers.FakeUser(
            access=["user", "admin"],
            username="test_admin2",
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        event = helpers.get_event(
            path="/portal/access/labs/test_admin2",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        response_body = json.loads(ret["body"])
        lab_access = response_body.get("labs")

        assert lab_access["lab_access"]["testlab"]["can_user_access_lab"]
        assert "testlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"]["protectedlab"]["can_user_access_lab"]
        assert "protectedlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"]["noaccess"]["can_user_access_lab"]
        assert "noaccess" in lab_access["viewable_labs_config"]

    def test_lab_access_geo_restricted_user(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"], username="test_admin")
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        targetuser = helpers.FakeUser(
            access=["user"],
            username="test_georestricted",
            country_code="SY",
            labs={
                "testlab": {
                    "lab_profiles": None,
                },
                "openlab": {
                    "lab_profiles": None,
                },
            },
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        event = helpers.get_event(
            path=f"/portal/access/labs/{targetuser.username}",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        response_body = json.loads(ret["body"])
        lab_access = response_body.get("labs")

        assert lab_access["lab_access"]["openlab"]["can_user_access_lab"]
        assert "openlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"]["testlab"]["can_user_access_lab"]
        assert "testlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"]["protectedlab"]["can_user_access_lab"]
        assert "protectedlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"].get("noaccess")
        assert "noaccess" not in lab_access["viewable_labs_config"]

    def test_lab_access_geo_restricted_admin(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"], username="test_admin")
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        targetuser = helpers.FakeUser(
            access=["user", "admin"],
            username="test_georestricted_admin",
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        event = helpers.get_event(
            path="/portal/access/labs/test_georestricted_admin",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        response_body = json.loads(ret["body"])
        lab_access = response_body.get("labs")

        assert lab_access["lab_access"]["testlab"]["can_user_access_lab"]
        assert "testlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"]["protectedlab"]["can_user_access_lab"]
        assert "protectedlab" in lab_access["viewable_labs_config"]

        assert not lab_access["lab_access"]["noaccess"]["can_user_access_lab"]
        assert "noaccess" in lab_access["viewable_labs_config"]

    def test_get_labs_of_a_user_user_not_found(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr(
            "portal.access.User",
            lambda *args, **kwargs: helpers.raise_error(
                error=UserNotFound(message="User not found")
            ),
        )

        event = helpers.get_event(
            path="/portal/access/labs/test_user2",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 404
        assert '"error": "User not found"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_get_json_all_users_of_a_lab(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        # Test lab doesn't exist
        event = helpers.get_event(
            path="/portal/access/users/testlab",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 404
        assert '"error": "\\"testlab\\" lab does not exist"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

        # Test lab does exist
        def lab_users_static(*args, **kwargs):
            return [
                {
                    "username": "test_user",
                    "email": "test@user.com",
                    "labs": {
                        "testlab": {
                            "lab_profiles": ["m6a.large"],
                        },
                    },
                }
            ]

        monkeypatch.setattr("portal.access.get_users_with_lab", lab_users_static)

        event = helpers.get_event(
            path="/portal/access/users/testlab",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)
        body = json.loads(ret["body"])

        assert ret["statusCode"] == 200
        assert body["users"] == [
            {
                "username": "test_user",
                "email": "test@user.com",
                "labs": {"testlab": {"lab_profiles": ["m6a.large"]}},
            }
        ]
        assert body["message"] == "OK"
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_filter_get_json_users_of_a_lab(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        REGION = os.getenv("STACK_REGION", "us-west-2")
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
        ## No need to delete the table between methods, it goes out of scope anyways.
        util.dynamo_db._DYNAMO_TABLE_USER = util.dynamo_db._DYNAMO_DB.Table(
            user_table_name
        )
        util.dynamo_db._DYNAMO_TABLE_LAB = util.dynamo_db._DYNAMO_DB.Table(
            lab_table_name
        )
        assert get_all_items(table_id="user") == [], "DB should be empty at the start"
        from objs.user.user import User

        user1 = User("test_user")
        setattr(user1, "email", "test@example.com")
        user1.add_lab(
            lab_short_name="testlab",
            lab_profiles="m6a.large",
        )
        user2 = User("test_user2")
        setattr(user2, "email", "test@mailhot.com")
        user2.add_lab(
            lab_short_name="testlab",
            lab_profiles="m6a.large",
        )
        user3 = User("super_cool_guy")
        setattr(user3, "email", "test@mailhot.com")
        user3.add_lab(
            lab_short_name="testlab",
            lab_profiles="m6a.large",
        )

        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)
        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        event = helpers.get_event(
            path="/portal/access/users/testlab",
            cookies=fake_auth,
            method="GET",
            qparams={"user_filter": "test_user"},
        )
        ret = main.lambda_handler(event, lambda_context)
        body = json.loads(ret["body"])

        assert ret["statusCode"] == 200
        unique_users = [entry["username"] for entry in body["users"]]
        assert unique_users == ["test_user", "test_user2"]
        assert body["message"] == "OK"
        assert ret["headers"].get("Content-Type") == "application/json"

        event = helpers.get_event(
            path="/portal/access/users/testlab",
            cookies=fake_auth,
            method="GET",
            qparams={"email_filter": "mailhot.com"},
        )
        ret = main.lambda_handler(event, lambda_context)
        body = json.loads(ret["body"])

        unique_users = [entry["username"] for entry in body["users"]]
        assert unique_users == ["super_cool_guy", "test_user2"]

        event = helpers.get_event(
            path="/portal/access/users/testlab",
            cookies=fake_auth,
            method="GET",
            qparams={"user_filter": "test", "email_filter": "mailhot.com"},
        )
        ret = main.lambda_handler(event, lambda_context)
        body = json.loads(ret["body"])

        unique_users = [entry["username"] for entry in body["users"]]
        assert unique_users == ["test_user2"]

    def test_set_user_labs_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)
        monkeypatch.setattr("util.manage_access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.manage_access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        body = {
            "labs": {
                "testlab": {
                    "lab_profiles": ["m6a.large"],
                }
            }
        }

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200, ret
        assert ret["body"].find('"labs": {') != -1
        assert ret["headers"].get("Content-Type") == "application/json"
        assert user.labs == {
            "testlab": {
                "lab_profiles": ["m6a.large"],
            }
        }

    def test_set_user_labs_bad_profile(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)
        monkeypatch.setattr("util.manage_access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.manage_access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        body = {
            "labs": {
                "noaccess": {
                    "lab_profiles": ["m6a.large"],
                }
            }
        }

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422, ret
        assert (
            ret["body"].find("\"Profile 'm6a.large' not allowed for lab noaccess\"")
            != -1
        )
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_set_user_labs_no_user(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr(
            "portal.access.User",
            lambda *args, **kwargs: helpers.raise_error(
                error=UserNotFound(message="User not found")
            ),
        )

        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        body = {
            "labs": {
                "testlab": {
                    "lab_profiles": ["m6a.large"],
                }
            }
        }

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 404
        assert '"error": "User not found"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_set_user_labs_malformed_json(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        body = "gadhahaafsdfsa"

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 400
        assert '"error": "Malformed JSON"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_set_user_labs_validate_payload(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)
        monkeypatch.setattr("util.manage_access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.manage_access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        # Missing "labs" key
        body = {}

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert '"result": "Does not contain \'labs\' key"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

        # No "Labs" to add:
        body = {"labs": {}}

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert '"result": "Success"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

        # Lab does not exist
        body = {
            "labs": {
                "lab_does_not_exist": {
                    "lab_profiles": ["m6a.large"],
                }
            }
        }

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert '"result": "Lab does not exist: lab_does_not_exist"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

        body = {"labs": {"testlab": {}}}

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert (
            '"result": "Field \'lab_profiles\' not provided for lab testlab"'
            in ret["body"]
        )
        assert ret["headers"].get("Content-Type") == "application/json"

        # Field incorrect type
        body = {
            "labs": {
                "testlab": {
                    "lab_profiles": "m6a.large",
                }
            }
        }

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert (
            "\"result\": \"Field 'lab_profiles' not of type <class 'list'>\""
            in ret["body"]
        )
        assert ret["headers"].get("Content-Type") == "application/json"

        # Lab profile does not exist
        ## To be implemented

    def test_set_user_labs_not_admin(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        body = {"labs": {}}

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert "User does not have required access" in ret["body"]
        assert ret["statusCode"] == 403
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_delete_user_labs_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("util.manage_access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.manage_access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)
        assert "testlab" in user.labs, (
            "Default lab should be in the user object already."
        )

        body = {
            "labs": {
                "testlab": {},
            }
        }

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="DELETE",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200, ret
        assert ret["body"].find('"labs": {') != -1
        assert ret["headers"].get("Content-Type") == "application/json"
        assert "testlab" not in user.labs, "Lab should be deleted after request."

    def test_delete_user_labs_malformed_json(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        body = "gadhahaafsdfsa"

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="DELETE",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 400
        assert '"error": "Malformed JSON"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_delete_user_labs_validate_payload(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        # Missing "labs" key
        body = {}

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="DELETE",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert '"result": "Does not contain \'labs\' key"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

        # No "Labs" to delete:
        body = {"labs": {}}

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="DELETE",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert '"result": "Success"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

        # Lab does not exist
        body = {
            "labs": {
                "lab_does_not_exist": {},
            }
        }

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="DELETE",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert '"result": "Lab does not exist: lab_does_not_exist"' in ret["body"]
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_delete_user_labs_not_admin(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        body = {"labs": {"testlab": {}}}

        event = helpers.get_event(
            body=json.dumps(body),
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="DELETE",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert "User does not have required access" in ret["body"]
        assert ret["statusCode"] == 403
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_application_button_availablility(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr(
            "conftest.BaseLabConfig.is_healthy", lambda *args, **kwargs: True
        )
        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        lab = helpers.FakeLab(access_requests=None)
        monkeypatch.setattr("portal.Lab", lambda *args, **kwargs: lab)

        event = helpers.get_event(
            path="/portal",
            cookies=fake_auth,
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert 'href="/portal/access/apply/testlab"' in ret["body"]

        lab = helpers.FakeLab(
            access_requests={
                "answers": [
                    {
                        "sar_experience": "answer1",
                        "osl_experience": "answer2",
                        "use_case": "answer3",
                        "what_science": "answer4",
                    },
                ],
                "status": "rejected",
            }
        )
        monkeypatch.setattr("portal.Lab", lambda *args, **kwargs: lab)

        event = helpers.get_event(
            path="/portal",
            cookies=fake_auth,
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert 'href="/portal/access/apply/testlab"' not in ret["body"]

    def test_application_auto_populate_active_application(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        user = helpers.FakeUser()
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        lab = helpers.FakeLab(
            access_requests={
                "answers": [
                    {
                        "sar_experience": "Nothing",
                        "osl_experience": "None",
                        "use_case": "For Science",
                        "what_science": "SAR",
                    },
                ],
                "status": "new",
            }
        )
        monkeypatch.setattr("portal.access.Lab", lambda *args, **kwargs: lab)

        event = helpers.get_event(
            path="/portal/access/apply/testlab",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ">Nothing</textarea>" in ret["body"]
        assert ret["body"].count("selected>") == 1

    def test_application_dont_autopopulate_non_active_application(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        monkeypatch.setattr("portal.access.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        user = helpers.FakeUser()
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        lab = helpers.FakeLab(
            access_requests={
                "answers": [
                    {
                        "sar_experience": "Nothing",
                        "osl_experience": "None",
                        "use_case": "For Science",
                        "what_science": "SAR",
                    },
                ],
                "status": "rejected",
            }
        )
        monkeypatch.setattr("portal.access.Lab", lambda *args, **kwargs: lab)

        event = helpers.get_event(
            path="/portal/access/apply/testlab",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert "></textarea>" in ret["body"]
        assert ret["body"].count("selected>") == 0
