import main

USER_TABLE_DATA = [
    {
        # Complete User
        "last_cookie_assignment": "2025-06-24 19:02:25",
        "created_at": "2025-06-09 20:49:22",
        "last_update": "2025-06-24 19:02:25",
        "profile": {},  # Not used for now
        "access": ["user"],
        "username": "GeneralUser",
        "require_profile_update": False,
    },
    {
        # Admin User
        "last_cookie_assignment": "2025-05-24 19:02:25",
        "created_at": "2025-05-09 20:49:22",
        "last_update": "2025-05-24 19:02:25",
        "profile": {},  # Not used for now
        "access": ["user", "admin"],
        "username": "AdminUser",
        "require_profile_update": False,
    },
    {
        # New, incomplete User
        "last_cookie_assignment": "2025-04-24 19:02:25",
        "created_at": "2025-04-09 20:49:22",
        "last_update": "2025-04-24 19:02:25",
        "profile": {},  # Not used for now
        "access": ["user"],
        "username": "NewUser",
        "require_profile_update": True,
    },
]


class TestUsersPages:
    # Ensure users page is not reachable if not logged in
    def test_users_not_logged_in(self, lambda_context, helpers):
        event = helpers.get_event(path="/portal/users")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302

    def test_users_nonadmin_logged_in(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["user"])

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.users.get_all_items", lambda: USER_TABLE_DATA)

        event = helpers.get_event(path="/portal/users", cookies=fake_auth)

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal"

    def test_users_admin_logged_in(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["admin", "user"])

        monkeypatch.setattr("portal.users.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.users.get_all_items", lambda: USER_TABLE_DATA)

        event = helpers.get_event(path="/portal/users", cookies=fake_auth)

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["body"].find("<b>YES</b>") != -1
        assert ret["body"].find("<b>GeneralUser</b>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_delete_invalid_cognito_user(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["admin", "user"])
        delete_user = "dne_user"

        monkeypatch.setattr("portal.users.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.users.get_all_items", lambda: USER_TABLE_DATA)
        monkeypatch.setattr(
            "util.cognito.delete_user_from_user_pool", lambda *args, **kwargs: True
        )
        monkeypatch.setattr(
            "util.user.dynamo_db.delete_item", lambda *args, **kwargs: False
        )

        event = helpers.get_event(
            path=f"/portal/users/delete/{delete_user}",
            cookies=fake_auth,
            method="post",
        )

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location", "").find("success=False") != -1

    def test_delete_invalid_dynamodb_user(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["admin", "user"])
        delete_user = "GeneralUser"

        monkeypatch.setattr("portal.users.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.users.get_all_items", lambda: USER_TABLE_DATA)
        monkeypatch.setattr(
            "util.cognito.delete_user_from_user_pool", lambda *args, **kwargs: True
        )
        monkeypatch.setattr(
            "util.user.dynamo_db.delete_item", lambda *args, **kwargs: False
        )

        event = helpers.get_event(
            path=f"/portal/users/delete/{delete_user}",
            cookies=fake_auth,
            method="post",
        )

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location", "").find("success=False") != -1

    def test_delete_invalid_admin_user(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["admin", "user"])
        delete_user = "AdminUser"

        monkeypatch.setattr("portal.users.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("portal.users.get_all_items", lambda: USER_TABLE_DATA)
        monkeypatch.setattr(
            "util.cognito.delete_user_from_user_pool", lambda *args, **kwargs: True
        )
        monkeypatch.setattr(
            "util.user.dynamo_db.delete_item", lambda *args, **kwargs: True
        )

        event = helpers.get_event(
            path=f"/portal/users/delete/{delete_user}",
            cookies=fake_auth,
            method="post",
        )

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location", "").find("success=False") != -1

    def test_delete_valid_user(self, lambda_context, monkeypatch, fake_auth, helpers):
        acting_user = helpers.FakeUser(access=["admin", "user"])
        delete_user = helpers.FakeUser(username="GeneralUser")

        monkeypatch.setattr("portal.users.User", lambda *args, **kwargs: delete_user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: acting_user)
        monkeypatch.setattr("portal.users.get_all_items", lambda: USER_TABLE_DATA)
        monkeypatch.setattr(
            "util.cognito.delete_user_from_user_pool", lambda *args, **kwargs: True
        )
        monkeypatch.setattr(
            "util.user.dynamo_db.delete_item", lambda *args, **kwargs: True
        )

        event = helpers.get_event(
            path=f"/portal/users/delete/{delete_user.username}",
            cookies=fake_auth,
            method="post",
        )

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location", "").find("success=True") != -1
