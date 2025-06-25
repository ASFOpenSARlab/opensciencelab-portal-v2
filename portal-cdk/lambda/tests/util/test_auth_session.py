import main


class TestAuthSession:
    def setup_method(self, _method):
        # We have to clear current_session, so it's reset between each test:
        from util.session import current_session

        current_session.auth = None
        current_session.user = None
        current_session.app = None

    def test_session_user_saved(
        self, lambda_context, monkeypatch, helpers, fake_auth, mocked_requests_post
    ):
        # Create FakeUser instance to be monkeypatched in and inspected after modified
        user = helpers.FakeUser()
        monkeypatch.setattr("main.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("requests.post", mocked_requests_post)
        monkeypatch.setattr("util.auth.validate_jwt", helpers.validate_jwt)
        monkeypatch.setattr(
            "aws_lambda_powertools.utilities.parameters.get_secret",
            lambda a: "er9LnqEOiH+JLBsFCy0kVeba6ZSlG903cliU7VYKnM8=",
        )
        from util.session import current_session

        event = helpers.get_event(
            path="/auth",
            qparams={
                "code": "good_code",
                "state": "/portal/profile",
            },
            cookies=fake_auth,
        )
        assert current_session.user is None, "User should not be set before handler"
        main.lambda_handler(event, lambda_context)
        assert current_session.user is not None, "User should be set after handler"
        assert current_session.user.username == "test_user", "Username should be set to 'test_user'"

    def test_session_no_cookie(
        self, lambda_context, monkeypatch, helpers, mocked_requests_post
    ):
        # Create FakeUser instance to be monkeypatched in and inspected after modified
        user = helpers.FakeUser()
        monkeypatch.setattr("main.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("requests.post", mocked_requests_post)
        monkeypatch.setattr("util.auth.validate_jwt", helpers.validate_jwt)
        monkeypatch.setattr(
            "aws_lambda_powertools.utilities.parameters.get_secret",
            lambda a: "er9LnqEOiH+JLBsFCy0kVeba6ZSlG903cliU7VYKnM8=",
        )
        from util.session import current_session

        event = helpers.get_event(
            path="/auth",
            qparams={
                "code": "good_code",
                "state": "/portal/profile",
            },
        )
        assert current_session.user is None, "User should not be set before handler"
        main.lambda_handler(event, lambda_context)
        assert current_session.user is None, (
            "User should still be None without a auth cookie"
        )

    def test_session_user_overridden(
        self, lambda_context, monkeypatch, helpers, mocked_requests_post
    ):
        # Create FakeUser instance to be monkeypatched in and inspected after modified
        user = helpers.FakeUser()
        monkeypatch.setattr("main.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("requests.post", mocked_requests_post)
        monkeypatch.setattr("util.auth.validate_jwt", helpers.validate_jwt)
        monkeypatch.setattr(
            "aws_lambda_powertools.utilities.parameters.get_secret",
            lambda a: "er9LnqEOiH+JLBsFCy0kVeba6ZSlG903cliU7VYKnM8=",
        )
        from util.session import current_session

        # Pretend this user is from a previous warm-start call:
        current_session.user = user
        # And this should override it, even if there's no cookie:
        event = helpers.get_event(
            path="/auth",
            qparams={
                "code": "good_code",
                "state": "/portal/profile",
            },
        )
        assert current_session.user == user, "User before handler should be generic"
        main.lambda_handler(event, lambda_context)
        assert current_session.user is None, (
            "User should still be None without a auth cookie"
        )
