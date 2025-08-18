import main
from util.exceptions import UserNotFound


class TestAccessPages:
    def test_user_manage_page(self, monkeypatch, lambda_context, helpers, fake_auth):
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

    def test_admin_manage_page(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        labs = helpers.FAKE_ALL_LABS
        monkeypatch.setattr("portal.access.all_labs", labs)

        def lab_users_static(*args, **kwargs):
            return ["test_user"]

        monkeypatch.setattr("portal.access.list_users_with_lab", lab_users_static)

        event = helpers.get_event(
            path="/portal/access/manage/testlab", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Test Lab") > -1
        # Add/refactor more asserts after manage page layout is figured out more
        assert (
            ret["body"].find(
                '<button type="submit" name="action" value="add">Add</button>'
            )
            > -1
        )
        assert (
            ret["body"].find(
                '<button type="submit" name="action" value="remove">Remove</button>'
            )
            > -1
        )
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_edituser(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        bodystr = {
            "username": "test_user",
            "lab_profiles": "",
            "time_quota": "",
            "lab_country_status": "",
            "can_user_see_lab_card": "on",
            "can_user_access_lab": "on",
            "action": "add",
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

    def test_get_user_labs_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="GET",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find('{"labs": {"testlab":') != -1
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_get_user_labs_no_user(
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
        assert ret["body"] == "User Not Found"
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_set_user_labs_correct(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.all_labs", helpers.FAKE_ALL_LABS)

        body = """
            {
                "labs": {
                    "testlab": {
                        "lab_profiles": ["m6a.large"],
                        "can_user_access_lab": true,
                        "can_user_see_lab_card": true,
                        "time_quota": "",
                        "lab_country_status": "protected"
                    }
                }
            }
            """

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find('"labs": {') != -1
        assert ret["headers"].get("Content-Type") == "application/json"
        assert user.labs == {
            "testlab": {
                "lab_profiles": ["m6a.large"],
                "can_user_access_lab": True,
                "can_user_see_lab_card": True,
                "time_quota": "",
                "lab_country_status": "protected"
            }
        }

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

        monkeypatch.setattr("portal.access.all_labs", helpers.FAKE_ALL_LABS)

        body = """
            {
                "labs": {
                    "testlab": {
                        "lab_profiles": ["m6a.large"],
                        "can_user_access_lab": true,
                        "can_user_see_lab_card": true,
                        "time_quota": "",
                        "lab_country_status": "protected"
                    }
                }
            }
            """

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 404
        assert ret["body"] == "User Not Found"
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_set_user_labs_malformed_json(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.all_labs", helpers.FAKE_ALL_LABS)

        body = """
            gadhahaafsdfsa
            """

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 400
        assert ret["body"] == '{"result": "Malformed JSON"}'
        assert ret["headers"].get("Content-Type") == "application/json"

    def test_set_user_labs_validate_payload(
        self, monkeypatch, lambda_context, helpers, fake_auth
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("portal.access.all_labs", helpers.FAKE_ALL_LABS)

        # Missing "labs" key
        body = "{}"

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert ret["body"] == '{"result": "Does not contain \'labs\' key"}'
        assert ret["headers"].get("Content-Type") == "application/json"

        # Lab does not exist
        body = """
            {
                "labs": {
                    "lab_does_not_exist": {
                        "lab_profiles": ["m6a.large"],
                        "can_user_access_lab": true,
                        "can_user_see_lab_card": true,
                        "time_quota": "",
                        "lab_country_status": "protected"
                    }
                }
            }
        """

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert ret["body"] == '{"result": "Lab does not exist: lab_does_not_exist"}'
        assert ret["headers"].get("Content-Type") == "application/json"

        # Missing field
        body = """
            {
                "labs": {
                    "testlab": {
                        "lab_profiles": ["m6a.large"],
                        "can_user_access_lab": true,
                        "can_user_see_lab_card": true,
                        "time_quota": ""
                    }
                }
            }
        """

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert (
            ret["body"] ==
            '{"result": "Field \'lab_country_status\' not provided for lab testlab"}'
        )
        assert ret["headers"].get("Content-Type") == "application/json"

        # Field incorrect type
        body = """
            {
                "labs": {
                    "testlab": {
                        "lab_profiles": ["m6a.large"],
                        "can_user_access_lab": [true],
                        "can_user_see_lab_card": true,
                        "time_quota": "",
                        "lab_country_status": "protected"
                    }
                }
            }
        """

        event = helpers.get_event(
            body=body,
            path="/portal/access/labs/test_user",
            cookies=fake_auth,
            method="PUT",
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 422
        assert (
            ret["body"] ==
            '{"result": "Field \'can_user_access_lab\' not of type <class \'bool\'>"}'
        )
        assert ret["headers"].get("Content-Type") == "application/json"

        # Lab profile does not exist
        ## To be implemented