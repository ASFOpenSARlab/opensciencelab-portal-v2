import main


class TestAccessPages:
    def test_user_manage_page(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(labs=["testlab"])
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        
        labs = helpers.LABS
        monkeypatch.setattr("portal.access.labs_dict", labs)
        
        event = helpers.get_event(path="/portal/access/manage/testlab", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        
        assert ret["statusCode"] == 302
        assert "User does not have required access" in ret["body"]
        assert ret["headers"].get("Location") == "/portal"
        assert ret["headers"].get("Content-Type") == "text/html"
    
    def test_admin_manage_page(self, monkeypatch, lambda_context, helpers, fake_auth):
        user = helpers.FakeUser(access=["user", "admin"], labs=["testlab"])
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)
        
        labs = helpers.LABS
        monkeypatch.setattr("portal.access.labs_dict", labs)
        
        def lab_users_static(*args, **kwargs):
            return ["test_user"]
        monkeypatch.setattr("portal.access.list_users_with_lab", lab_users_static)
        
        event = helpers.get_event(path="/portal/access/manage/testlab", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        
        assert ret["statusCode"] == 200
        assert ret["body"].find("Test Lab") > -1
        # Add/refactor more asserts after manage page layout is figured out more
        assert ret["body"].find('<button type="submit" name="action" value="add">Add</button>') > -1
        assert ret["body"].find('<button type="submit" name="action" value="remove">Remove</button>') > -1
        assert ret["headers"].get("Content-Type") == "text/html"
        