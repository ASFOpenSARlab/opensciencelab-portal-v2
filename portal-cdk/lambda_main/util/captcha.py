import requests
import os
import json

from aws_lambda_powertools import Logger

logger = Logger(child=True)

def submit_captcha_challenge(site_token:str) -> float:
    # Get reCAPTCHA score
    secret_key = os.getenv("RECAPTCHA_SECRET_KEY")
    url = "https://www.google.com/recaptcha/api/siteverify"
    resp = requests.post(
        url=url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"secret": secret_key, "response": site_token},
    )
    resp_body = json.loads(resp.text)
    # Log reCAPTCHA response
    # print({"recaptcha": resp.json()})
    # logger.info({"recaptcha": resp.json()})
    # If response is bad or unsuccessful
    if resp.status_code != 200 or not resp_body["success"]:
        return -1.0
    # Return score
    return float(resp_body["score"])