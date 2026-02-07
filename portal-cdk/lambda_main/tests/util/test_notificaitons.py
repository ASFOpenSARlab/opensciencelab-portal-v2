import pytest
import logging

from util.notifications import get_notifications

# This will break tests in 2046
MOCK_CALENDAR_CONTENT = """
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
DESCRIPTION:---<br>scopes: test <br>tags: home<br>type: info<br>placement: top-full-width<br>---<br>&lt\;p&gt\;This is a test notification&lt\;/p&gt\;
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Active event on "test" scope
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
BEGIN:VEVENT
CREATED:20260121T215531Z
SEQUENCE:0
DTSTART;VALUE=DATE:20260116
DTEND;VALUE=DATE:20460125
DTSTAMP:20260206T231124Z
DESCRIPTION:---<br>scopes: test <br>tags: test_tag<br>type: info<br>placement: top-full-width<br>---<br>&lt\;p&gt\;This is a test notification&lt\;/p&gt\;
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Second active event on "test" scope
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
BEGIN:VEVENT
CREATED:20260121T215531Z
SEQUENCE:0
DTSTART;VALUE=DATE:20160116
DTEND;VALUE=DATE:20160125
DTSTAMP:20260206T231124Z
DESCRIPTION:---<br>scopes: test <br>tags: other_tag<br>type: info<br>placement: top-full-width<br>---<br>&lt\;p&gt\;This is a test notification&lt\;/p&gt\;
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
DESCRIPTION:---<br>scopes: otherscope <br>tags: home<br>type: info<br>placement: top-full-width<br>---<br>&lt\;p&gt\;This is a test notification&lt\;/p&gt\;
LAST-MODIFIED:20260122T183908Z
STATUS:CONFIRMED
SUMMARY:Active Event on "otherscope" Scope
TRANSP:TRANSPARENT
UID:18ncht0pnm4hct8icu05g54g81@google.com
END:VEVENT
"""

MOCK_CALENDAR_MALFORMED_CONTENT = """
BEGIN:VCALENDAR
X-WR-CALNAME:test-cal
"""

MOCK_CALENDAR_MALFORMED_EVENT_CONTENT = """
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
DESCRIPTION:---<br>scopes: test <br>tags: home<br>type: info<br>placement: top-full-width<br>---<br>&lt\;p&gt\;This is a test notification&lt\;/p&gt\;
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


class TestPortalNotifications:
    def test_get_active_events(self, monkeypatch):
        # Test that only active events for "test" scope are returned
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
            {
                "title": 'Second active event on "test" scope',
                "message": "<p>This is a test notification</p>",
                "type": "info",
                "placement": "top-full-width"
            },
            {
                "title": 'Active event on "test" scope',
                "message": "<p>This is a test notification</p>",
                "type": "info",
                "placement": "top-full-width",
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
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert (
            caplog.records[0].message == "Malformed event description: I AM MALFORMED"
        )
        assert active_events == [
            {
                "title": "Active correctly formatted event",
                "message": "<p>This is a test notification</p>",
                "type": "info",
                "placement": "top-full-width",
            }
        ]

    def test_event_filtering(self, monkeypatch):
        # Only active event with "test_tag" is returned
        def mock_get(url):
            class MockResponse:
                def __init__(self):
                    self.ok = True
                    self.status_code = 200
                    self.text = MOCK_CALENDAR_CONTENT

            return MockResponse()

        monkeypatch.setattr("util.notifications.requests.get", mock_get)

        active_events = get_notifications("test", "test_tag")
        assert active_events == [
            {
                "title": 'Second active event on "test" scope',
                "message": "<p>This is a test notification</p>",
                "type": "info",
                "placement": "top-full-width",
            }
        ]

    def test_get_calendar_error(self, monkeypatch):
        def mock_get(url):
            class MockResponse:
                def __init__(self):
                    self.ok = False
                    self.status_code = 400
                    self.text = ""

            return MockResponse()

        monkeypatch.setattr("util.notifications.requests.get", mock_get)

        active_events = get_notifications("test", "test_tag")
        assert active_events == []
