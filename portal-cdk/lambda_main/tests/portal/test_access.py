import main


class TestAccessPages:
    def test_user_manage_page(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        labs = helpers.LABS
        monkeypatch.setattr("portal.access.labs_dict", labs)

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

        labs = helpers.LABS
        monkeypatch.setattr("portal.access.labs_dict", labs)

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
                'username': 'test_user',
                'lab_profiles': '',
                'time_quota': '',
                'lab_country_status': '',
                'can_user_see_lab_card': 'on',
                'can_user_access_lab': 'on',
                'action': 'add'
            }
        monkeypatch.setattr("portal.access.form_body_to_dict", lambda *args, **kwargs: bodystr)
        
        event = helpers.get_event(
            path="/portal/access/manage/testlab2/edituser",
            cookies=fake_auth,
            body="placeholder",
            method="POST"
        )
        ret = main.lambda_handler(event, lambda_context)
        
        assert "testlab2" in user.labs
        assert user.labs["testlab2"] == {
            'lab_profiles': '',
            'time_quota': '',
            'lab_country_status': '',
            'can_user_access_lab': True,
            'can_user_see_lab_card': True
            }
        
        assert ret["statusCode"] == 302
        assert ret["headers"].get("Location") == "/portal/access/manage/testlab2"
        assert ret["headers"].get("Content-Type") == "text/html"
