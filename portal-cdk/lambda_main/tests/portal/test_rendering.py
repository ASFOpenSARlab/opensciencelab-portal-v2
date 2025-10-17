import main


class TestRenderingTemplates:
    # Ensure users page is not reachable if not logged in
    def test_users_not_logged_in(self, lambda_context, helpers):
        event = helpers.get_event(path="/")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["body"].find("Welcome to OpenScienceLab") != -1
        assert ret["body"].find('href="/portal/profile">Profile') == -1

    def test_normal_users_logged_in(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

        event = helpers.get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert not ret["headers"].get("Location")
        assert ret["body"].find('href="/portal/profile">Profile') > -1
        assert ret["body"].find('href="/portal/users">Manage Users') == -1

    def test_admin_users_logged_in(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["user", "admin"])
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

        event = helpers.get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["body"].find('href="/portal/profile">Profile') > -1
        assert ret["body"].find('href="/portal/users">Manage Users') > -1

    def test_georestricted_user_displayed_labs(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(
            country_code="AF",
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
            }
        )
        print("USER")
        print(user.country_code)
        print(user.labs)
        print(helpers.FAKE_LABS["testlab"].ip_country_status)
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

        event = helpers.get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        with open("out.txt", 'w') as f:
            f.write(str(ret))
        assert ret["statusCode"] == 200
        assert ret["body"].find('href="/portal/profile">Profile') > -1
        assert ret["body"].find('href="/portal/users">Manage Users') > -1
