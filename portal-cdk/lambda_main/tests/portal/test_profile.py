from urllib.parse import urlencode
from base64 import b64encode

import main
import portal.profile


class TestProfilePages:
    # Ensure profile page is not reachable if not logged in
    def test_profile_logged_out(self, lambda_context, helpers):
        event = helpers.get_event(path="/portal/profile/form/test_user")
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User is not logged in"
        assert (
            ret["headers"]
            .get("Location")
            .endswith("?return=/portal/profile/form/test_user")
        )
        assert ret["headers"].get("Content-Type") == "text/html"

    # Ensure page loads if logged in
    def test_profile_logged_in(self, lambda_context, monkeypatch, fake_auth, helpers):
        user = helpers.FakeUser()

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(
            path="/portal/profile/form/test_user", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Hello <i>test_user</i>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"

    # Ensure users gets redirected to THEIR profile
    def test_profile_logged_in_root_redirect(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser()

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(path="/portal/profile", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "Redirecting to User Profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    def test_user_access_other_profile(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser()

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(
            path="/portal/profile/form/not_my_username", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Content-Type") == "text/html"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    def test_no_user_access(self, lambda_context, monkeypatch, fake_auth, helpers):
        user = helpers.FakeUser(access=[])
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(
            path="/portal/profile/form/test_user", cookies=fake_auth
        )
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["headers"].get("Content-Type") == "text/html"
        assert ret["headers"].get("Location") == "/portal"

    # Test query params trigger missing value and autofill values correctly
    def test_profile_query_params(
        self, lambda_context, monkeypatch, fake_auth, helpers
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        qparams = {
            "country_of_residence_error": "missing",
            "is_affiliated_with_nasa_error": "missing",
            "is_affiliated_with_us_gov_research_error": "missing",
            "is_affliated_with_isro_research_error": "missing",
            "is_affliated_with_university_error": "missing",
            "country_of_residence": "default",
            "is_affiliated_with_nasa": "default",
            "user_or_pi_nasa_email": "default",
            "user_affliated_with_nasa_research_email": "",
            "pi_affliated_with_nasa_research_email": "",
            "is_affiliated_with_us_gov_research": "default",
            "user_affliated_with_gov_research_email": "",
            "is_affliated_with_isro_research": "default",
            "user_affliated_with_isro_research_email": "",
            "is_affliated_with_university": "yes",
            "faculty_member_affliated_with_university": True,
            "research_member_affliated_with_university": False,
            "graduate_student_affliated_with_university": False,
        }
        path = "/portal/profile/form/test_user"
        event = helpers.get_event(path=path, cookies=fake_auth, qparams=qparams)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find('<p class="warning">Value is missing</p>') != -1
        assert (
            ret["body"].find('data-id-to-show="university_affiliations"\nselected')
            != -1
        )
        assert (
            ret["body"].find('name="faculty_member_affliated_with_university"\nchecked')
            != -1
        )
        assert ret["headers"].get("Content-Type") == "text/html"

    # Test profile autofills from existing profile correctly
    def test_profile_loading(self, lambda_context, monkeypatch, fake_auth, helpers):
        profile = {
            "user_affliated_with_nasa_research_email": "",
            "pi_affliated_with_nasa_research_email": "apple@apple.com",
            "research_member_affliated_with_university": False,
            "country_of_residence": "US",
            "user_affliated_with_isro_research_email": "grabulon@gooble.com",
            "faculty_member_affliated_with_university": True,
            "is_affliated_with_isro_research": "yes",
            "is_affiliated_with_us_gov_research": "yes",
            "user_affliated_with_gov_research_email": "zippo@zip.com",
            "graduate_student_affliated_with_university": False,
            "is_affiliated_with_nasa": "yes",
            "is_affliated_with_university": "yes",
            "user_or_pi_nasa_email": "no",
        }
        user = helpers.FakeUser(profile=profile)

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal/profile/form/test_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["headers"].get("Content-Type") == "text/html"
        # Check that each value has been filled correctly
        assert ret["body"].find('<option value="US" selected>') != -1
        assert (
            ret["body"].find('data-id-to-show="user_or_pi_nasa_email_div"\nselected')
            != -1
        )
        assert ret["body"].find('data-id-to-show="pi_nasa_email"\nselected>') != -1
        assert ret["body"].find('value="apple@apple.com"') != -1
        assert ret["body"].find('data-id-to-show="user_gov_email"\nselected>') != -1
        assert ret["body"].find('value="zippo@zip.com"') != -1
        assert ret["body"].find('data-id-to-show="user_isro_email"\nselected>') != -1
        assert ret["body"].find('value="grabulon@gooble.com"') != -1
        assert (
            ret["body"].find('data-id-to-show="university_affiliations"\nselected')
            != -1
        )
        assert (
            ret["body"].find('name="faculty_member_affliated_with_university"\nchecked')
            != -1
        )

    # Ensure the profile dict is properly validated
    def test_validate_profile_dict(self):
        ## No fields filled
        profile_dict = {
            "country_of_residence": "default",
            "is_affiliated_with_nasa": "default",
            "is_affiliated_with_us_gov_research": "default",
            "is_affliated_with_isro_research": "default",
            "is_affliated_with_university": "default",
        }
        correct, errors = portal.profile.validate_profile_dict(profile_dict)

        expected_errors = {
            "country_of_residence_error": "missing",
            "is_affiliated_with_nasa_error": "missing",
            "is_affiliated_with_us_gov_research_error": "missing",
            "is_affliated_with_isro_research_error": "missing",
            "is_affliated_with_university_error": "missing",
        }
        assert not correct
        assert errors == expected_errors

        ## NASA affiliation errors
        # not specify if user or pi is affiliated with nasa
        profile_dict = {
            "country_of_residence": "United States",
            "is_affiliated_with_nasa": "yes",
            "user_or_pi_nasa_email": "default",
            "is_affiliated_with_us_gov_research": "no",
            "is_affliated_with_isro_research": "no",
            "is_affliated_with_university": "no",
        }
        correct, errors = portal.profile.validate_profile_dict(profile_dict)

        expected_errors = {
            "user_or_pi_nasa_email_error": "missing",
        }
        assert not correct
        assert errors == expected_errors

        # not provide user nasa email
        profile_dict = {
            "country_of_residence": "United States",
            "is_affiliated_with_nasa": "yes",
            "user_or_pi_nasa_email": "yes",
            "user_affliated_with_nasa_research_email": "",
            "is_affiliated_with_us_gov_research": "no",
            "is_affliated_with_isro_research": "no",
            "is_affliated_with_university": "no",
        }
        correct, errors = portal.profile.validate_profile_dict(profile_dict)

        expected_errors = {
            "user_affliated_with_nasa_research_email_error": "missing",
        }
        assert not correct
        assert errors == expected_errors

        # not provide pi nasa email
        profile_dict = {
            "country_of_residence": "United States",
            "is_affiliated_with_nasa": "yes",
            "user_or_pi_nasa_email": "no",
            "pi_affliated_with_nasa_research_email": "",
            "is_affiliated_with_us_gov_research": "no",
            "is_affliated_with_isro_research": "no",
            "is_affliated_with_university": "no",
        }
        correct, errors = portal.profile.validate_profile_dict(profile_dict)

        expected_errors = {
            "pi_affliated_with_nasa_research_email_error": "missing",
        }
        assert not correct
        assert errors == expected_errors

        ## government affiliation errors
        profile_dict = {
            "country_of_residence": "United States",
            "is_affiliated_with_nasa": "no",
            "is_affiliated_with_us_gov_research": "yes",
            "user_affliated_with_gov_research_email": "",
            "is_affliated_with_isro_research": "no",
            "is_affliated_with_university": "no",
        }
        correct, errors = portal.profile.validate_profile_dict(profile_dict)

        expected_errors = {
            "user_affliated_with_gov_research_email_error": "missing",
        }
        assert not correct
        assert errors == expected_errors

        ## ISRO affiliation errors
        profile_dict = {
            "country_of_residence": "United States",
            "is_affiliated_with_nasa": "no",
            "is_affiliated_with_us_gov_research": "no",
            "is_affliated_with_isro_research": "yes",
            "user_affliated_with_isro_research_email": "",
            "is_affliated_with_university": "no",
        }
        correct, errors = portal.profile.validate_profile_dict(profile_dict)

        expected_errors = {
            "user_affliated_with_isro_research_email_error": "missing",
        }
        assert not correct
        assert errors == expected_errors

        ## Test correct filling
        profile_dict = {
            "country_of_residence": "United States",
            "is_affiliated_with_nasa": "yes",
            "user_or_pi_nasa_email": "yes",
            "user_affliated_with_nasa_research_email": "email@email.com",
            "is_affiliated_with_us_gov_research": "yes",
            "user_affliated_with_gov_research_email": "email@email.com",
            "is_affliated_with_isro_research": "yes",
            "user_affliated_with_isro_research_email": "email@email.com",
            "is_affliated_with_university": "yes",
        }
        correct, errors = portal.profile.validate_profile_dict(profile_dict)

        expected_errors = {}
        assert correct
        assert errors == expected_errors

    # Ensure profile form is converted to a python dict correctly
    def test_process_profile_form(self, monkeypatch):
        ## Correct Filling
        def validate_profile_true(query_dict: dict) -> tuple[bool, dict[str, str]]:
            return True, {}

        monkeypatch.setattr(
            "portal.profile.validate_profile_dict", validate_profile_true
        )

        # request_body is a base64 encoded query string
        query_string: str = "country_of_residence=US&is_affiliated_with_nasa=no&is_affiliated_with_us_gov_research=no&is_affliated_with_isro_research=no&is_affliated_with_university=yes&faculty_member_affliated_with_university=on"
        request_body = b64encode(query_string.encode("utf-8"))
        success, query_dict = portal.profile.process_profile_form(request_body)

        expected_dict = {
            "country_of_residence": "US",
            "is_affiliated_with_nasa": "no",
            "is_affiliated_with_us_gov_research": "no",
            "is_affliated_with_isro_research": "no",
            "is_affliated_with_university": "yes",
            "faculty_member_affliated_with_university": True,
            "research_member_affliated_with_university": False,
            "graduate_student_affliated_with_university": False,
        }
        assert success
        assert query_dict == expected_dict

        ## Incorrect filling
        def validate_profile_false(query_dict: dict) -> tuple[bool, dict[str, str]]:
            return False, {"is_affiliated_with_nasa_error": "missing"}

        monkeypatch.setattr(
            "portal.profile.validate_profile_dict", validate_profile_false
        )

        # request_body is a base64 encoded query string
        query_string: str = "country_of_residence=US&is_affiliated_with_nasa=default&is_affiliated_with_us_gov_research=no&is_affliated_with_isro_research=no&is_affliated_with_university=yes&faculty_member_affliated_with_university=on"
        request_body = b64encode(query_string.encode("utf-8"))
        success, query_dict = portal.profile.process_profile_form(request_body)

        expected_dict = {
            "country_of_residence": "US",
            "is_affiliated_with_nasa": "default",
            "is_affiliated_with_nasa_error": "missing",
            "is_affiliated_with_us_gov_research": "no",
            "is_affliated_with_isro_research": "no",
            "is_affliated_with_university": "yes",
            "faculty_member_affliated_with_university": True,
            "research_member_affliated_with_university": False,
            "graduate_student_affliated_with_university": False,
        }
        assert not success
        assert query_dict == expected_dict

    # Ensure that incorrect profile fillings redirect to profile page, correct filling redirect to portal
    def test_profile_user_filled(self, monkeypatch, lambda_context, fake_auth, helpers):
        username = "test_user"

        user = helpers.FakeUser(profile={})
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        ## Test correct filling
        def process_profile_form_correct(
            *args, **kwargs
        ) -> tuple[bool, dict[str, str]]:
            return True, {
                "country_of_residence": "US",
                "is_affiliated_with_nasa": "no",
                "is_affiliated_with_us_gov_research": "no",
                "is_affliated_with_isro_research": "no",
                "is_affliated_with_university": "yes",
                "faculty_member_affliated_with_university": True,
                "research_member_affliated_with_university": False,
                "graduate_student_affliated_with_university": False,
            }

        monkeypatch.setattr(
            "portal.profile.process_profile_form", process_profile_form_correct
        )
        query_dict = {
            "country_of_residence": "US",
            "is_affiliated_with_nasa": "no",
            "user_or_pi_nasa_email": "default",
            "user_affliated_with_nasa_research_email": "",
            "pi_affliated_with_nasa_research_email": "",
            "is_affiliated_with_us_gov_research": "no",
            "user_affliated_with_gov_research_email": "",
            "is_affliated_with_isro_research": "no",
            "user_affliated_with_isro_research_email": "",
            "is_affliated_with_university": "no",
        }
        query_string: str = urlencode(query_dict)
        request_body = b64encode(query_string.encode("utf-8"))

        event = helpers.get_event(
            path=f"/portal/profile/form/{username}",
            method="POST",
            body=request_body,
            cookies=fake_auth,
        )

        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "\"{'Redirect to /portal'}\""

        ## Test wrong filling
        def process_profile_form_wrong(*args, **kwargs) -> tuple[bool, dict[str, str]]:
            return False, {
                "country_of_residence": "US",
                "is_affiliated_with_nasa": "default",
                "is_affiliated_with_nasa_error": "missing",
                "is_affiliated_with_us_gov_research": "no",
                "is_affliated_with_isro_research": "no",
                "is_affliated_with_university": "yes",
                "faculty_member_affliated_with_university": True,
                "research_member_affliated_with_university": False,
                "graduate_student_affliated_with_university": False,
            }

        monkeypatch.setattr(
            "portal.profile.process_profile_form", process_profile_form_wrong
        )
        query_dict = {
            "country_of_residence": "US",
            "is_affiliated_with_nasa": "no",
            "user_or_pi_nasa_email": "default",
            "user_affliated_with_nasa_research_email": "",
            "pi_affliated_with_nasa_research_email": "",
            "is_affiliated_with_us_gov_research": "no",
            "user_affliated_with_gov_research_email": "",
            "is_affliated_with_isro_research": "no",
            "user_affliated_with_isro_research_email": "",
            "is_affliated_with_university": "no",
        }
        query_string: str = urlencode(query_dict)
        request_body = b64encode(query_string.encode("utf-8"))

        event = helpers.get_event(
            path=f"/portal/profile/form/{username}",
            method="POST",
            body=request_body,
            cookies=fake_auth,
        )
        ret = main.lambda_handler(event, lambda_context)

        expected_query_dict = {
            "country_of_residence": "US",
            "is_affiliated_with_nasa": "default",
            "is_affiliated_with_nasa_error": "missing",
            "is_affiliated_with_us_gov_research": "no",
            "is_affliated_with_isro_research": "no",
            "is_affliated_with_university": "yes",
            "faculty_member_affliated_with_university": "True",
            "research_member_affliated_with_university": "False",
            "graduate_student_affliated_with_university": "False",
        }
        expected_query_string = urlencode(expected_query_dict)

        assert ret["statusCode"] == 302
        assert (
            ret["body"]
            == f"\"{{'Redirect to /portal/profile/form/test_user?{expected_query_string}'}}\""
        )

    def test_profile_redirect(self, monkeypatch, lambda_context, fake_auth, helpers):
        user = helpers.FakeUser(require_profile_update=True)
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User must update profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"


class TestProfileAccess:
    # Test user accessing other profile
    def test_user_access_other_profile(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal/profile/form/other_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "\"{'Redirect to /portal/profile/form/test_user'}\""
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    # Test user accessing own profile
    def test_user_access_own_profile(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal/profile/form/test_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Hello <i>test_user</i>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"

    # Test user redirect for required profile filling
    def test_user_profile_redirect_flag(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True)
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User must update profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    # Test user accessing other profile while required to fill own profile
    def test_user_access_other_profile_must_fill_own(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True)
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal/profile/form/test_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Hello <i>test_user</i>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"

    # Test admin accessing other profile
    def test_admin_access_other_profile(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        admin_user = helpers.FakeUser(username="admin_user", access=["admin", "user"])
        profile_user = helpers.FakeUser(username="other_user", access=["user"])

        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: admin_user)
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: profile_user)

        path = "/portal/profile/form/other_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 200
        assert ret["body"].find("Hello <i>other_user</i>") != -1
        assert ret["headers"].get("Content-Type") == "text/html"
        # Admin should see settings for other_user:
        assert ret["body"].find('Admin Settings') > -1

    # Test admin redirect for required profile filling
    def test_admin_profile_redirect_flag(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True, access=["admin", "user"])
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User must update profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    # Test admin accessing other profile while required to fill own profile
    def test_admin_access_other_profile_must_fill_own(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(require_profile_update=True, access=["admin", "user"])
        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        path = "/portal/profile/form/other_user"
        event = helpers.get_event(path=path, cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        assert ret["statusCode"] == 302
        assert ret["body"] == "User must update profile"
        assert ret["headers"].get("Location") == "/portal/profile/form/test_user"

    def test_normal_user_no_table(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser()

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(path="/portal/profile/form/test_user", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert not ret["headers"].get("Location")
        assert ret["body"].find('Admin Settings') == -1

    def test_admin_user_with_table(
        self, monkeypatch, lambda_context, fake_auth, helpers
    ):
        user = helpers.FakeUser(access=["user", "admin"])

        monkeypatch.setattr("portal.profile.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        event = helpers.get_event(path="/portal/profile/form/test_user", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)
        assert ret["statusCode"] == 200
        assert ret["body"].find('Admin Settings') > -1


