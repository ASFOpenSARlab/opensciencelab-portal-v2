import main
from util.exceptions import UserNotFound
import json
import pytest


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
                            "can_user_see_lab_card": True,
                            "can_user_access_lab": True,
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
            "can_user_see_lab_card": "on",
            "can_user_access_lab": "on",
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
            "can_user_access_lab": True,
            "can_user_see_lab_card": True,
        }

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal/access/manage/testlab2"
        assert ret["headers"].get("Content-Type") == "text/html"

        # Remove user seeing lab card
        bodystr = {
            "username": "test_user",
            "action": "toggle_can_user_see_lab_card",
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
            "can_user_access_lab": True,
            "can_user_see_lab_card": False,
        }

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal/access/manage/testlab2"
        assert ret["headers"].get("Content-Type") == "text/html"

        # Remove user lab access
        bodystr = {
            "username": "test_user",
            "action": "toggle_can_user_access_lab",
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
            "can_user_access_lab": False,
            "can_user_see_lab_card": False,
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
        lab_access_list = response_body.get("labs")

        assert ret["statusCode"] == 200
        assert any(
            lab_acccess.get("lab").get("short_lab_name") == "testlab"
            for lab_acccess in lab_access_list
        )
        assert any(
            lab_acccess.get("lab").get("short_lab_name") == "differentlab"
            for lab_acccess in lab_access_list
        )
        assert any(
            lab_acccess.get("lab").get("short_lab_name") == "noaccess"
            for lab_acccess in lab_access_list
        )
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
                    "can_user_see_lab_card": True,
                    "can_user_access_lab": True,
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
        lab_access_list = response_body.get("labs")

        assert ret["statusCode"] == 200
        assert any(
            lab_acccess.get("lab").get("short_lab_name") == "testlab"
            for lab_acccess in lab_access_list
        )
        assert any(
            lab_acccess.get("lab").get("short_lab_name") == "differentlab"
            for lab_acccess in lab_access_list
        )
        assert all(
            lab_acccess.get("lab").get("short_lab_name") != "noaccess"
            for lab_acccess in lab_access_list
        )
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_get_labs_order(self, monkeypatch, lambda_context, helpers, fake_auth):
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
                    "can_user_see_lab_card": True,
                    "can_user_access_lab": True,
                },
                "differentlab": {
                    "time_quota": None,
                    "lab_profiles": None,
                    "lab_country_status": None,
                    "can_user_see_lab_card": True,
                    "can_user_access_lab": True,
                },
                # protectedlab is deliberately not here, it should be rendered after
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
        lab_access_list = response_body.get("labs")

        for i, lab in enumerate(lab_access_list):
            if lab.get("lab").get("short_lab_name") == "differentlab":
                differentlab_index = i
            if lab.get("lab").get("short_lab_name") == "protectedlab":
                protectedlab_index = i

        assert ret["statusCode"] == 200
        assert "differentlab_index" in locals()
        assert "protectedlab_index" in locals()
        assert differentlab_index < protectedlab_index
        assert ret["headers"].get("Content-Type") == "application/json"

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

    def test_get_all_users_of_a_lab(
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
                    "can_user_access_lab": True,
                    "can_user_see_lab_card": True,
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
                "can_user_access_lab": True,
                "can_user_see_lab_card": True,
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
                    "can_user_access_lab": True,
                    "can_user_see_lab_card": True,
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
                    "can_user_access_lab": True,
                    "can_user_see_lab_card": True,
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
                    "can_user_access_lab": True,
                    "can_user_see_lab_card": True,
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
                    "can_user_access_lab": True,
                    "can_user_see_lab_card": True,
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
                    "lab_profiles": ["m6a.large"],
                    "can_user_access_lab": [True],
                    "can_user_see_lab_card": True,
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
            "\"result\": \"Field 'can_user_access_lab' not of type <class 'bool'>\""
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
