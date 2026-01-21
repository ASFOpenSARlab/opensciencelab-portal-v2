import os
import requests
from ics import Calendar
import datetime
import yaml
import html2text
import re

from aws_lambda_powertools import Logger

logger = Logger(child=True)

CALENDAR_URL: str = os.getenv("CALENDAR_URL")


# def get_notifications(notification_source:str, display_locations:str):
def get_notifications(scope: str, tag: str | None = None):
    try:
        # Download Calendar
        resp = requests.get(CALENDAR_URL)
        if resp.status_code != 200:
            return []

        cal = Calendar(resp.text)

        # Process calendar events
        active_events = []

        now_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        compiled_regex = re.compile("---(.*)---(.*)$", re.DOTALL)
        for event in list(cal.events):
            begin_time = event.begin.to("utc").datetime.replace(tzinfo=None)
            end_time = event.end.to("utc").datetime.replace(tzinfo=None)

            if begin_time <= now_time <= end_time:
                # Process event description
                groups = compiled_regex.search(event.description)

                # TODO ERROR HANDLING

                meta: dict = yaml.safe_load(html2text.html2text(groups.group(1)))
                message: str = html2text.html2text(groups.group(2))

                # Check if requested scope in allowed scopes for notification
                allowed_scopes = [scope.strip() for scope in meta["scopes"].split(",")]
                if scope not in allowed_scopes:
                    continue

                # Check if requested tag in allowed tags for notification
                allowed_tags = [tag.strip() for tag in meta["tags"].split(",")]
                if tag and tag not in allowed_tags:
                    continue

                active_events.append(
                    {
                        "title": event.name,
                        "message": message.strip(),
                        "type": meta["type"].strip(),
                        "placement": meta.get("placement", "top-full-width").strip(),
                    }
                )
    except Exception as e:
        err_str = f"Something went wrong: {e}"
        logger.error(err_str)
        raise ValueError(err_str)
    return active_events
