import os

import boto3
from aws_lambda_powertools import Logger

from util.auth import decrypt_data
from util.user import User
from util.format import jinja_template

logger = Logger(child=True)

_sesv2 = None


def get_sesv2() -> None:
    global _sesv2
    if not _sesv2:
        _sesv2 = boto3.client("sesv2", region_name=os.environ.get("region"))
    return _sesv2


def _get_user_email_for_username(username: str) -> str:
    if not username:
        return None

    # Since osl-admin is a special username, make sure we override with the admin email
    if username == "osl-admin":
        return os.getenv("SES_EMAIL")

    try:
        user = User(username, create_if_missing=False)
    except Exception:
        logger.error(f"User {username} not found")
        return None

    return user.email


def _parse_email_message(data: dict) -> dict:
    """
    Parse sent POST payload into a dictionary of email parameters

    Return dict of form:

    {
        "from": ["",],
        "to": ["",],
        "reply_to": ["",],
        "cc": ["",],
        "bcc": ["",],
        "subject": "",
        "html_body": ""
    }

    """

    email_meta = {}

    ####  To
    to_email = data["to"].get("email", [])
    if isinstance(to_email, str):
        to_email = [to_email]

    to_username = data["to"].get("username", [])
    if isinstance(to_username, str):
        to_username = [to_username]
    for user in to_username:
        user_email = _get_user_email_for_username(username=user)
        if user_email:
            to_email.append(user_email)

    if not to_email:
        raise Exception("No TO user specified")

    email_meta["to"] = to_email

    ####  CC
    cc = data.get("cc", None)
    if cc:
        cc_email = cc.get("email", [])
        if isinstance(cc_email, str):
            cc_email = [cc_email]

        cc_username = cc.get("username", [])
        if isinstance(cc_username, str):
            cc_username = [cc_username]
        for user in cc_username:
            user_email = _get_user_email_for_username(username=user)
            if user_email:
                cc_email.append(user_email)

        email_meta["cc"] = cc_email

    ####  BCC
    bcc = data.get("bcc", None)
    if bcc:
        bcc_email = bcc.get("email", [])
        if isinstance(bcc_email, str):
            bcc_email = [bcc_email]

        bcc_username = bcc.get("username", [])
        if isinstance(bcc_username, str):
            bcc_username = [bcc_username]

        for user in bcc_username:
            user_email = _get_user_email_for_username(username=user)
            if user_email:
                bcc_email.append(user_email)

        email_meta["bcc"] = bcc_email

    ####  FROM
    ## It will be assumed that all emails will be FROM only one user and one REPLY-TO.
    ## Therefore the FROM will always be overriden and all inputed FROM parameters will be ignored.
    email_meta["reply_to"] = [os.getenv("SES_EMAIL")]
    email_meta["from"] = f'"OpenScienceLab" <admin@{os.getenv("SES_DOMAIN")}>'

    #### subject
    data_subject = data.get("subject", "")
    if data_subject:
        email_meta["subject"] = data_subject

    data_body = data.get("html_body", "")

    if data_body:
        email_meta["html_body"] = jinja_template(
            {"data_body": data_body}, "user_email.html.j2"
        )

    return email_meta


def send_user_email(request_data):
    sesv2: boto3.Client = get_sesv2()

    try:
        decrypted_data: dict = decrypt_data(request_data)

        parsed_data: dict = _parse_email_message(decrypted_data)

        sesv2.send_email(
            FromEmailAddress=parsed_data.get("from", ""),
            Destination={
                "ToAddresses": parsed_data.get("to", []),
                "CcAddresses": parsed_data.get("cc", []),
                "BccAddresses": parsed_data.get("bcc", []),
            },
            ReplyToAddresses=parsed_data.get("reply_to", []),
            Content={
                "Simple": {
                    "Subject": {
                        "Data": parsed_data.get("subject", ""),
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Html": {
                            "Data": parsed_data.get("html_body", ""),
                            "Charset": "UTF-8",
                        },
                    },
                },
            },
        )

        result = "Success"
    except Exception as e:
        logger.error(f"Could not send email: {e}")
        logger.info("Sending admin error email...")

        html_body = jinja_template({"error": e}, "error_email.html.j2")

        sesv2.send_email(
            FromEmailAddress=f'"OpenScienceLab" <admin@{os.getenv("SES_DOMAIN")}>',
            Destination={
                "ToAddresses": [os.getenv("SES_EMAIL")],
            },
            ReplyToAddresses=[os.getenv("SES_EMAIL")],
            Content={
                "Simple": {
                    "Subject": {
                        "Data": "Error in sending email",
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Html": {
                            "Data": html_body,
                            "Charset": "UTF-8",
                        },
                    },
                },
            },
        )

        result = "Error"

    return result
