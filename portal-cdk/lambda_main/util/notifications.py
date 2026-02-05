import os
import requests
from ics import Calendar
import datetime
import yaml
import html2text
import re

from aws_lambda_powertools import Logger
from util.log_timer import measure_time

logger = Logger(child=True)

CALENDAR_URL: str = os.getenv("CALENDAR_URL")


def get_notifications(scope: str, filter_tag: str = "all"):
    try:
        logger.info(f"Notification calendar URL: {CALENDAR_URL}")
        logger.info(f"Notification calendar requested {scope=} {filter_tag=}")

        # Download Calendar
        with measure_time(service="calendar", action="load calendar data"):
            resp = requests.get(CALENDAR_URL)
        if resp.status_code != 200:
            return []

        cal = Calendar(resp.text)

        active_events = []

        now_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        compiled_regex = re.compile("---(.*)---(.*)$", re.DOTALL)
        for event in list(cal.events):
            begin_time = event.begin.to("utc").datetime.replace(tzinfo=None)
            end_time = event.end.to("utc").datetime.replace(tzinfo=None)

            if begin_time <= now_time <= end_time:
                # Process event description
                groups = compiled_regex.search(event.description)

                # If the event description is not formatted properly then either the grouping will fail or the yaml parser
                # Then an expection will be thrown
                meta: dict = yaml.safe_load(html2text.html2text(groups.group(1)))
                message: str = html2text.html2text(groups.group(2))

                # Check if requested scope in allowed scopes for notification
                allowed_scopes = [s.strip() for s in meta["scopes"].split(",")]
                if scope not in allowed_scopes:
                    logger.info(
                        f"Notification calendar non-matching scope: {meta=} {message=}"
                    )
                    continue

                # Check if requested tag in allowed tags for notification
                # If requested tag is 'all' or calendar tags have 'all', always keep event
                allowed_tags = [t.strip() for t in meta.get("tags", "all").split(",")]
                if not (
                    filter_tag == "all"
                    or "all" in allowed_tags
                    or filter_tag in allowed_tags
                ):
                    logger.info(
                        f"Notification calendar non-matching tag: {meta=} {message=}"
                    )
                    continue

                active_event = {
                    "title": event.name,
                    "message": message.strip(),
                    "type": meta["type"].strip(),
                    "placement": meta.get("placement", "top-full-width").strip(),
                }
                logger.info(f"Notification calendar event: {meta=} {message=}")

                active_events.append(active_event)

        # Remove duplicates and order
        unique_events = [dict(t) for t in set(tuple(d.items()) for d in active_events)]
        active_events = sorted(unique_events, key=lambda x: x["title"], reverse=True)

    except Exception as e:
        err_str = f"Something went wrong: {e}"
        logger.error(err_str)
        raise ValueError(err_str)

    return active_events
