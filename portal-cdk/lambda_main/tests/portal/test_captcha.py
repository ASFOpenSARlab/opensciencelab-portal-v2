from unittest.mock import Mock
from datetime import datetime
import json
import os

import boto3
from moto import mock_aws

import main
from util.exceptions import UserNotFound
from data import DATE_F
from conftest import MockResponse


class TestCaptcha:
    def test_submit_captcha_success(
        self, monkeypatch, lambda_context, helpers, fake_auth, 
    ):
        from util.captcha import submit_captcha_challenge

        def post_request_response(*args, **kwargs) -> MockResponse:
            data = {
                    "success": True,
                    "challenge_ts": "1999-00-00T00:00:00Z",
                    "hostname": "osl-deployment.cloudfront.net",
                    "score": 0.4,
                    "action": "submit_mfa",
                }
            return MockResponse(
                status_code=200,
                text_data=json.dumps(data),
                json_data=data,
            )

        monkeypatch.setattr("util.captcha.requests.post", post_request_response)
        
        score = submit_captcha_challenge("SITE_TOKEN")
        assert score == 0.4

    def test_submit_captcha_recaptcha_fail(
        self, monkeypatch, lambda_context, helpers, fake_auth, 
    ):
        from util.captcha import submit_captcha_challenge

        def post_request_response(*args, **kwargs) -> MockResponse:
            data = {
                    "success": False,
                }
            return MockResponse(
                status_code=200,
                text_data=json.dumps(data),
                json_data=data,
            )            
        
        monkeypatch.setattr("util.captcha.requests.post", post_request_response)
        
        score = submit_captcha_challenge("SITE_TOKEN")
        assert score == -1.0

    def test_submit_captcha_response_fail(
        self, monkeypatch, lambda_context, helpers, fake_auth, 
    ):
        from util.captcha import submit_captcha_challenge

        def post_request_response(*args, **kwargs) -> MockResponse:
            data = {
                    "success": False,
                }
            return MockResponse(
                status_code=500,
                text_data=json.dumps(data),
                json_data=data,
            )            
        
        monkeypatch.setattr("util.captcha.requests.post", post_request_response)
        
        score = submit_captcha_challenge("SITE_TOKEN")
        assert score == -1.0