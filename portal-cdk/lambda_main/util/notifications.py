import os
import requests

PROD_CALENDAR = ""
NON_PROD_CALENDAR = ""

if os.getenv("IS_PROD", "false").lower() == "true":
    CALENDAR: str = PROD_CALENDAR
else:
    CALENDAR: str = NON_PROD_CALENDAR


def get_notes():
  CALENDAR
  pass