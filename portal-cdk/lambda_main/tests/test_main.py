import main


class TestPortalIntegrations:
    def test_landing_handler(self, lambda_context, helpers):
        event = helpers.get_event()

        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert "Welcome to OpenScienceLab" in ret["body"]
        assert "Log in" in ret["body"]
        assert "/login?client_id=fake-cognito-id&response_type=code" in ret["body"]

    def test_not_logged_in(self, lambda_context, helpers):
        event = helpers.get_event(path="/portal")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 302
        assert ret["body"] == "User is not logged in"
        assert ret["headers"].get("Location").endswith("?return=/portal")
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_static_image_dne(self, lambda_context, helpers):
        event = helpers.get_event(path="/static/img/dne.png")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 404

    def test_static_image_bad_type(self, lambda_context, helpers):
        event = helpers.get_event(path="/static/foo/bar.zip")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 404

    def test_static_image(self, lambda_context, helpers):
        event = helpers.get_event(path="/static/img/jh_logo.png")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "image/png"

        event = helpers.get_event(path="/static/js/require.js")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "text/javascript"

        event = helpers.get_event(path="/static/css/style.min.css")
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "text/css"

    def test_user_home_page(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

        event = helpers.get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find('<div id="lab-choices">') != -1
        assert ret["body"].find('href="/portal/access/manage/testlab"') == -1
        assert ret["headers"].get("Location") is None
        assert ret["headers"].get("Content-Type") == "text/html"

    def test_admin_home_page(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(access=["admin", "user"], labs={"testlab": {}})
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("util.user.user.LABS", helpers.FAKE_LABS)

        event = helpers.get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find('<div id="lab-choices">') != -1
        assert ret["body"].find('href="/portal/access/manage/testlab"') >= -1
        assert ret["headers"].get("Location") is None
        assert ret["headers"].get("Content-Type") == "text/html"
