"""
This file sets up ENV VARs for tests

https://stackoverflow.com/a/50610630/21674565
"""

import os
import copy
import time

import pytest
from dataclasses import dataclass, field
import datetime

os.environ["STACK_REGION"] = "us-west-2"
os.environ["COGNITO_CLIENT_ID"] = "fake-cognito-id"
os.environ["COGNITO_POOL_ID"] = "fake-pool-id"
from util.auth import PORTAL_USER_COOKIE, COGNITO_JWT_COOKIE
from util.labs import BaseLab, LabAccessInfo
from util.user.user import filter_lab_access, create_lab_structure


def MockedRequestsPost(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    json_response_payload = {}
    if kwargs["data"]["code"] == "good_code":
        json_response_payload = {
            "id_token": "valid_id_token",
            "access_token": "valid_access_token",
            "refresh_token": "valid_refresh_token",
        }

    if args[0].endswith("/oauth2/token"):
        return MockResponse(json_response_payload, 200)

    return MockResponse(None, 404)


@pytest.fixture
def mocked_requests_post() -> MockedRequestsPost:
    return MockedRequestsPost


@pytest.fixture
def fake_auth(monkeypatch):
    # Bypass JWT
    validate_jwt = Helpers().validate_jwt
    tokens = {
        "access_token": "valid_access_token",
        "id_token": "valid_id_token",
    }
    monkeypatch.setattr(
        "util.auth.get_tokens_from_refresh",
        lambda *args, **kwargs: tokens,
    )
    monkeypatch.setattr("util.auth.validate_jwt", validate_jwt)
    monkeypatch.setattr("jwt.decode", validate_jwt)

    # Override signing key
    monkeypatch.setattr(
        "aws_lambda_powertools.utilities.parameters.get_secret",
        lambda a: "er9LnqEOiH+JLBsFCy0kVeba6ZSlG903cliU7VYKnM8=",
    )

    auth_cookies = {PORTAL_USER_COOKIE: "bla", COGNITO_JWT_COOKIE: "bla"}

    return auth_cookies


BASIC_REQUEST = {
    "rawPath": "/test",
    "requestContext": {
        "requestContext": {"requestId": "227b78aa-779d-47d4-a48e-ce62120393b8"},
        "http": {"method": "GET", "path": "/test"},
        "stage": "$default",
    },
    "queryStringParameters": {},
    "cookies": [],
}


@dataclass
class Helpers:
    @staticmethod
    def get_event(
        path="/", method="GET", cookies=None, headers=None, qparams=None, body=None
    ):
        # This rather than defaulting to polluted dicts
        cookies = {} if not cookies else cookies
        headers = {} if not headers else headers
        qparams = {} if not qparams else qparams
        ret_event = copy.deepcopy(BASIC_REQUEST)

        # Update request path/method
        ret_event["rawPath"] = path
        ret_event["requestContext"]["http"]["path"] = path
        ret_event["requestContext"]["http"]["method"] = method

        if body:
            ret_event["body"] = body

        for name, value in cookies.items():
            ret_event["cookies"].append(f"{name}={value}")

        for key, value in qparams.items():
            ret_event["queryStringParameters"][key] = value

        return ret_event

    @staticmethod
    def validate_jwt(*args, **kwargs):
        return {
            "client_id": "2pjp68mov6sfhqda8pjphll8cq",
            "token_use": "access",
            "auth_time": time.time(),
            "exp": time.time() + 100,
            "iat": time.time() - 100,
            "username": "test_user",
            # email comes from id_token
            "email": "test_user@user.com",
        }

    @dataclass
    class FakeUser:
        username: str = field(default_factory=lambda: "test_user")
        profile: dict = field(
            default_factory=lambda: {
                "country_of_residence": "US",
                "faculty_member_affliated_with_university": False,
                "graduate_student_affliated_with_university": False,
                "is_affiliated_with_nasa": "no",
                "is_affiliated_with_us_gov_research": "no",
                "is_affliated_with_isro_research": "no",
                "is_affliated_with_university": "no",
                "pi_affliated_with_nasa_research_email": "",
                "research_member_affliated_with_university": False,
                "user_affliated_with_gov_research_email": "",
                "user_affliated_with_isro_research_email": "",
                "user_affliated_with_nasa_research_email": "",
                "user_or_pi_nasa_email": "default",
            }
        )
        last_cookie_assignment: str = None
        access: list = field(default_factory=lambda: ["user"])
        require_profile_update: bool = False
        labs: dict = field(
            default_factory=lambda: {
                "testlab": {
                    "time_quota": None,
                    "lab_profiles": None,
                    "lab_country_status": None,
                    "can_user_see_lab_card": True,
                    "can_user_access_lab": True,
                },
                "noaccess": {
                    "time_quota": None,
                    "lab_profiles": None,
                    "lab_country_status": None,
                    "can_user_see_lab_card": False,
                    "can_user_access_lab": False,
                },
            }
        )
        email: str = field(default_factory=lambda: "fakeemail@email.com")
        _rec_counter: int = field(default_factory=lambda: 1)
        is_locked: bool = False
        create_if_missing: bool = True

        def update_last_cookie_assignment(self) -> None:
            self.last_cookie_assignment = datetime.datetime(
                2024, 1, 1, 12, 0, 0
            ).strftime("%Y-%m-%d %H:%M:%S")

        def is_admin(self) -> bool:
            return "admin" in self.access

        def remove_user(self) -> bool:
            return True

        def set_labs(self, formatted_labs: dict) -> None:
            self.labs = formatted_labs

        def add_lab(self, **kwargs):
            self.labs[kwargs["lab_short_name"]] = create_lab_structure(**kwargs)

        def remove_lab(self, lab_short_name: str):
            self.labs[lab_short_name] = None

        def get_lab_access(self) -> list[LabAccessInfo]:
            return filter_lab_access(
                is_admin=self.is_admin(),
                all_labs_in=Helpers.FAKE_ALL_LABS,
                labs=self.labs,
            )

    FAKE_ALL_LABS = {
        "testlab": BaseLab(friendly_name="Test Lab", short_lab_name="testlab"),
        "noaccess": BaseLab(friendly_name="No Access Lab", short_lab_name="noaccess"),
    }

    # Raises a given error, used for monkeypatching
    # set kwarg "error" to your error
    def raise_error(*args, **kwargs):
        raise kwargs.get("error", Exception("Cannot get error from kwargs"))


@pytest.fixture
def helpers():
    return Helpers()
