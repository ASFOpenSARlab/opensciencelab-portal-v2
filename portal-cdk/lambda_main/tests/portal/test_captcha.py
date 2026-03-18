# from datetime import datetime
# import json
# import os

# import boto3
# from moto import mock_aws

# import main
# from util.exceptions import UserNotFound
# from data import DATE_F


# @mock_aws
# class TestCaptcha:
#     def test_submit_captcha(
#         self, monkeypatch, lambda_context, helpers, fake_auth
#     ):
#         from util.captcha import submit_captcha_challenge

#         def post_request_response(*args, **kwargs) -> dict:
#             return {
#                 "text"
#             }
#         {
#                 "success": True,
#                 "challenge_ts": "2026-03-18T00:53:46Z",
#                 "hostname": "d374u2hfpypbv2.cloudfront.net",
#                 "score": 0.3,
#                 "action": "submit_mfa"
#             }
        
#         monkeypatch.setattr("util.captcha.requests.post", post_request_response)
        
#         score = submit_captcha_challenge("SITE_TOKEN")

#         print("GOOP")
#         print(score)
#         assert False