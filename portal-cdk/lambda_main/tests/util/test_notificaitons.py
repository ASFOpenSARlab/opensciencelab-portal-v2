import os
import pytest
import logging
import json

import boto3
from moto import mock_aws

from util.notifications import get_notifications

REGION = os.getenv("STACK_REGION", "us-west-2")
USER_IP_LOGS_GROUP_NAME = "FAKE_USER_IP_LOGS_GROUP_NAME"
USER_IP_LOGS_STREAM_NAME = "FAKE_USER_IP_LOGS_STREAM_NAME"

# This will break tests in 2046
MOCK_CALENDAR_CONTENT="""
BEGIN:VCALENDAR
X-WR-CALNAME:test-cal
X-WR-TIMEZONE:America/Anchorage
X-WR-CALDESC:A Test Calendar
VERSION:2.0
PRODID:-//Google Inc//Google Calendar 70.9054//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
CREATED:20260121T215531Z
SEQUENCE:0
DTSTART;VALUE=DATE:20260116
DTEND;VALUE=DATE:20460125
DTSTAMP:20260206T231124Z
DESCRIPTION:---<br>sc<span>opes: test</span><span><span><span><span><span><span> </span></span></span></span></span></span><span><span><span><span><span><span><br>type: info<br>placement: bottom-full-width<br>---<br>&lt\;p&gt\;</span></span></span></span>This is a test notification&lt\;/p&gt\;</span></span><br>&lt\;p&gt\;Its cool<span><span><span><span><span><span>&lt\;/p&gt\;</span></span></span></span></span></span>
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Active Event on "test" Scope
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
BEGIN:VEVENT
CREATED:20260121T215531Z
SEQUENCE:0
DTSTART;VALUE=DATE:20160116
DTEND;VALUE=DATE:20160125
DTSTAMP:20260206T231124Z
DESCRIPTION:---<br>sc<span>opes: test</span><span><span><span><span><span><span> </span></span></span></span></span></span><span><span><span><span><span><span><br>type: info<br>placement: bottom-full-width<br>---<br>&lt\;p&gt\;</span></span></span></span>This is a test notification&lt\;/p&gt\;</span></span><br>&lt\;p&gt\;Its cool<span><span><span><span><span><span>&lt\;/p&gt\;</span></span></span></span></span></span>
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Expired Event
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
BEGIN:VEVENT
CREATED:20260121T215531Z
SEQUENCE:0
DTSTART;VALUE=DATE:20260116
DTEND;VALUE=DATE:20460125
DTSTAMP:20260206T231124Z
DESCRIPTION:---<br>sc<span>opes: otherscope</span><span><span><span><span><span><span> </span></span></span></span></span></span><span><span><span><span><span><span><br>type: info<br>placement: bottom-full-width<br>---<br>&lt\;p&gt\;</span></span></span></span>This is a test notification&lt\;/p&gt\;</span></span><br>&lt\;p&gt\;Its cool<span><span><span><span><span><span>&lt\;/p&gt\;</span></span></span></span></span></span>
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Active Event on "otherscope" Scope
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
"""

MOCK_CALENDAR_MALFORMED_CONTENT="""
BEGIN:VCALENDAR
X-WR-CALNAME:test-cal
"""

MOCK_CALENDAR_MALFORMED_EVENT_CONTENT="""
BEGIN:VCALENDAR
X-WR-CALNAME:test-cal
X-WR-TIMEZONE:America/Anchorage
X-WR-CALDESC:A Test Calendar
VERSION:2.0
PRODID:-//Google Inc//Google Calendar 70.9054//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
CREATED:20260121T215531Z
SEQUENCE:0
DTSTART;VALUE=DATE:20260116
DTEND;VALUE=DATE:20460125
DTSTAMP:20260206T231124Z
DESCRIPTION:---<br>sc<span>opes: test</span><span><span><span><span><span><span> </span></span></span></span></span></span><span><span><span><span><span><span><br>type: info<br>placement: bottom-full-width<br>---<br>&lt\;p&gt\;</span></span></span></span>This is a test notification&lt\;/p&gt\;</span></span><br>&lt\;p&gt\;Its cool<span><span><span><span><span><span>&lt\;/p&gt\;</span></span></span></span></span></span>
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Active correctly formatted event
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
BEGIN:VEVENT
CREATED:20260121T215531Z
SEQUENCE:0
DTSTART;VALUE=DATE:20260116
DTEND;VALUE=DATE:20460125
DTSTAMP:20260206T231124Z
DESCRIPTION:I AM MALFORMED
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Active malformed event
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
"""

@mock_aws
class TestPortalNotifications:
    def test_get_active_events(self, monkeypatch):
        # Test that only active event for "test" scope is returned
        # Expired event and event on "otherscope" scope are not returned
        def mock_get(url):
            class MockResponse:
                def __init__(self):
                    self.ok = True
                    self.status_code = 200
                    self.text = MOCK_CALENDAR_CONTENT
            return MockResponse()
        monkeypatch.setattr("util.notifications.requests.get", mock_get)
        active_events = get_notifications("test")
        assert active_events == [
            {'title': 'Active Event on "test" Scope',
             'message': '<p>This is a test notification</p>  \n<p>Its cool</p>',
             'type': 'info',
             'placement': 'bottom-full-width'
            }
        ]

    def test_error_handling(self, monkeypatch):
        def mock_get(url):
            class MockResponse:
                def __init__(self):
                    self.ok = True
                    self.status_code = 200
                    self.text = MOCK_CALENDAR_MALFORMED_CONTENT
            return MockResponse()
        monkeypatch.setattr("util.notifications.requests.get", mock_get)
        
        with pytest.raises(ValueError) as err:
            get_notifications("test")
        assert str(err.value) == "Something went wrong: A VCALENDAR must have at least one PRODID"

    def test_malformed_event_description(self, monkeypatch, caplog):
        def mock_get(url):
            class MockResponse:
                def __init__(self):
                    self.ok = True
                    self.status_code = 200
                    self.text = MOCK_CALENDAR_MALFORMED_EVENT_CONTENT
            return MockResponse()
        monkeypatch.setattr("util.notifications.requests.get", mock_get)

        with caplog.at_level(logging.ERROR):
            active_events = get_notifications("test")
        assert caplog.records[0].levelname == "ERROR"
        assert caplog.records[0].message == "Malformed event description: I AM MALFORMED"
        assert active_events == [
            {'title': 'Active correctly formatted event',
             'message': '<p>This is a test notification</p>  \n<p>Its cool</p>',
             'type': 'info',
             'placement': 'bottom-full-width'
            }
        ]