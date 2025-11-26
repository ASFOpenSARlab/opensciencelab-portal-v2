import main
from util.exceptions import UserNotFound
from moto import mock_aws
import boto3
import os
import json
import pytest


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
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        labs = helpers.FAKE_LABS
        monkeypatch.setattr("portal.access.LABS", labs)

        def lab_users_static(*args, **kwargs):
            return [
                {
                    "username": "test_user",
                    "labs": {
                        "testlab": {
                            "lab_profiles": ["m6a.large"],
                        },
                    },
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
                '<button type="submit" name="action" value="remove_user">Remove</button>'
            )
            > -1
        )
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_admin_editing_user(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        # Adding lab
        bodystr = {
            "username": "test_user",
            "lab_profiles": "",
            "time_quota": "",
            "lab_country_status": "",
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
            "time_quota": None,
            "lab_country_status": "",
        }

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal/access/manage/testlab2"
        assert ret["headers"].get("Content-Type") == "text/html"

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

        with pytest.raises(ValueError) as exc_info:
            ret = main.lambda_handler(event, lambda_context)

        assert str(exc_info.value) == "Invalid action"

    def test_get_labs_of_a_user_admin_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

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
                    "time_quota": None,
                    "lab_profiles": None,
                    "lab_country_status": None,
                },
            },
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

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
                    "time_quota": None,
                    "lab_profiles": None,
                    "lab_country_status": None,
                },
                # protectedlab is deliberately not here, it should be marked as able to see but not access
                # noaccess is deliberately not here, should not be present
            },
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

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

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

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

        assert lab_access["lab_access"]["protectedlab"]["can_user_access_lab"]
        assert "protectedlab" in lab_access["viewable_labs_config"]

        assert lab_access["lab_access"]["noaccess"]["can_user_access_lab"]
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
                    "time_quota": None,
                    "lab_profiles": None,
                    "lab_country_status": None,
                },
                "openlab": {
                    "time_quota": None,
                    "lab_profiles": None,
                    "lab_country_status": None,
                },
            },
        )
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: targetuser)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

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

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

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

        assert lab_access["lab_access"]["protectedlab"]["can_user_access_lab"]
        assert "protectedlab" in lab_access["viewable_labs_config"]

        assert lab_access["lab_access"]["noaccess"]["can_user_access_lab"]
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

        util.user.dynamo_db._DYNAMO_CLIENT = boto3.client(
            "dynamodb",
            region_name=REGION,
        )
        util.user.dynamo_db._DYNAMO_DB = boto3.resource(
            "dynamodb",
            region_name=REGION,
        )
        
        
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
        from util.user.user import User
        user1 = User("test_user")
        user1.add_lab(lab_short_name="testlab", lab_profiles="m6a.large", time_quota=None, lab_country_status="something")
        user2 = User("test_user2")
        user2.add_lab(lab_short_name="testlab", lab_profiles="m6a.large", time_quota=None, lab_country_status="something")
        user3 = User("super_cool_guy")
        user3.add_lab(lab_short_name="testlab", lab_profiles="m6a.large", time_quota=None, lab_country_status="something")
        
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)
        monkeypatch.setattr("util.user.dynamo_db.LABS", helpers.FAKE_LABS)

        event = helpers.get_event(
            path="/portal/access/users/testlab",
            cookies=fake_auth,
            method="GET",
            qparams={"filter":"test_user"}
        )
        ret = main.lambda_handler(event, lambda_context)
        body = json.loads(ret["body"])

        assert ret["statusCode"] == 200
        unique_users = [entry["username"] for entry in body["users"]]
        assert unique_users == ["test_user", "test_user2"]
        assert body["message"] == "OK"
        assert ret["headers"].get("Content-Type") == "application/json"


    def test_set_user_labs_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

        body = {
            "labs": {
                "testlab": {
                    "lab_profiles": ["m6a.large"],
                    "time_quota": "",
                    "lab_country_status": "protected",
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
                "time_quota": "",
                "lab_country_status": "protected",
            }
        }

    def test_set_user_labs_bad_profile(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

        body = {
            "labs": {
                "noaccess": {
                    "lab_profiles": ["m6a.large"],
                    "time_quota": "",
                    "lab_country_status": "protected",
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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

        body = {
            "labs": {
                "testlab": {
                    "lab_profiles": ["m6a.large"],
                    "time_quota": "",
                    "lab_country_status": "protected",
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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

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
                    "time_quota": "",
                    "lab_country_status": "protected",
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

        # Missing field "lab_country_status"
        body = {
            "labs": {
                "testlab": {
                    "lab_profiles": ["m6a.large"],
                    "time_quota": "",
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
            '"result": "Field \'lab_country_status\' not provided for lab testlab"'
            in ret["body"]
        )
        assert ret["headers"].get("Content-Type") == "application/json"

        # Field incorrect type
        body = {
            "labs": {
                "testlab": {
                    "lab_profiles": "m6a.large",
                    "time_quota": "",
                    "lab_country_status": "protected",
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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)
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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

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

        monkeypatch.setattr("portal.access.LABS", helpers.FAKE_LABS)

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
