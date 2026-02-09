"""Lab Class to abstract the rest of the code using the database."""

import datetime

from util.exceptions import LabDoesNotExist, InvalidLabRequestStatus
from util.labs import LAB_CONFIGS
from util.session import current_session
from util.auth import get_ip_and_country
from util.dynamo_db import (
    get_item,
    create_item,
    update_item,
    get_all_items,
    dynamo_filter,
)
from objs.base_db_table import Table

from .defaults import defaults
from .validator_map import validator_map

LAB_TABLE_ID = "lab"
REQ_TABLE_ID = "request"
LAB_TABLE_KEY = "labname"
USER_TABLE_KEY = "username"

VALID_REQUEST_STATUSES = ["new", "approved", "rejected", "pending"]
LOCKED_REQUEST_STATUSES = ["approved", "rejected"]
DEFAULT_ACCESS_QUESTIONS = [
    "sar_experience",
    "osl_experience",
    "use_case",
    "personal_impacts",
    "community_impacts",
    "research_impacts",
]


class Lab(Table):
    def __init__(self, labname: str):
        # Create a Lab Table
        super().__init__(
            unique_key_value=labname,
            unique_key_name=LAB_TABLE_KEY,
            table_id=LAB_TABLE_ID,
            defaults=defaults,
            validator_map=validator_map,
        )

        # Mark the id
        super().__setattr__(LAB_TABLE_KEY, labname)

        # Apply anything in the DB:
        db_info = get_item(key={LAB_TABLE_KEY: self.labname}, table_id=LAB_TABLE_ID)

        # Error if the lab isn't valid
        if not db_info and self.labname not in LAB_CONFIGS:
            raise LabDoesNotExist(
                f"Lab {self.labname} does not exist.",
            )

        # Create item in the DB, if it doesn't exist, and it's in LAB_CONFIGS
        if not db_info:
            create_item(
                key={LAB_TABLE_KEY: self.labname},
                item=defaults,
                table_id=LAB_TABLE_ID,
            )
            db_info = {}

        ## Load all attributes in to the class:
        #  (self instead of super, so it DOES hit the method below).
        for key in validator_map:
            if key in db_info:
                # You just loaded it to the DB, the one time you don't have to save it:
                self.__setattr__(key, db_info[key], _save=False)
            else:
                self.__setattr__(key, None)

    def get_access_request(self, username: str) -> dict:
        """

        Args:
            username: Username to fetch an access request for a lab

        Returns: Dict of all copies of the user's answers
            {
              "answers": [  # List of Dicts so we can allow updating and keep a record.
                {
                  "sar_experience": "...",
                  "osl_experience": "...",
                  "use_case": "...",
                  "personal_impacts": "...",
                  "community_impacts": "...",
                  "research_impacts": "...",
                  "submission_date": "...",
                  "submission_ip": "...",
                  "submission_cc": "...",
                },
              ],
              "status": "new|approved|rejected|pending",
            }

        """
        # Pull any existing row from the db
        req_dict = get_item(
            key={
                LAB_TABLE_KEY: self.labname,
                USER_TABLE_KEY: username,
            },
            table_id=REQ_TABLE_ID,
        )

        return req_dict

    def _put_access_request(self, request: dict, username: str) -> None:
        """

        Args:
            request: Full request payload
            username: username

        Don't call directory. Use add_access_request()

        """
        existing_req = self.get_access_request(username)
        if not existing_req:
            create_item(
                key={
                    LAB_TABLE_KEY: self.labname,
                    USER_TABLE_KEY: username,
                },
                item=request,
                table_id=REQ_TABLE_ID,
            )
        else:
            # Don't allow updating "finalized" status.
            if existing_req.get("status") in LOCKED_REQUEST_STATUSES:
                raise InvalidLabRequestStatus(
                    f"Attempt to update request in status {existing_req.get('status')}"
                )
            update_item(
                key={
                    LAB_TABLE_KEY: self.labname,
                    USER_TABLE_KEY: username,
                },
                updates=request,
                table_id=REQ_TABLE_ID,
            )

    def add_access_request(self, answers: dict, username: str) -> None:
        """

        Args:
            answers:
                {
                    "sar_experience": "...",
                    "osl_experience": "...",
                    "use_case": "...",
                    "personal_impacts": "...",
                    "community_impacts": "...",
                    "research_impacts": "...",
                  }
            username:
                "username"
        """
        # Pull any existing row from the db
        req_dict = self.get_access_request(username=username)

        # If it doesn't exist, stub it out
        if not req_dict:
            req_dict = {
                "status": "new",
                "answers": [],
            }

        # Copy in received answers
        answers_dict = {}
        for question in DEFAULT_ACCESS_QUESTIONS:
            answers_dict[question] = answers.get(question)

        # Add user metadata fields:
        ip_address, country_code = get_ip_and_country(current_session.app.current_event)
        answers_dict["submission_ip"] = ip_address
        answers_dict["submission_cc"] = country_code
        answers_dict["submission_date"] = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Add answers to the end of the list
        req_dict["answers"].append(answers_dict)

        # Save record
        self._put_access_request(req_dict, username)

    def set_access_request_status(self, username: str, status: str):
        """

        Args:
            username: User with an existing access request
            status: New status to update request to

        """
        if status not in VALID_REQUEST_STATUSES:
            raise InvalidLabRequestStatus(
                f"Status '{status}' not in {VALID_REQUEST_STATUSES}"
            )

        req_dict = self.get_access_request(username=username)
        if not req_dict:
            raise InvalidLabRequestStatus(
                f"User {username} has not requested access to {self.labname}"
            )

        # Don't update if the status hasn't actually changed
        if req_dict["status"] == status:
            return

        # Change Status
        req_dict["status"] = status
        self._put_access_request(req_dict, username)

    def get_requests(self, status: str | list | None = None):
        filters = dynamo_filter(attr_name=LAB_TABLE_KEY, filter_value=self.labname)

        if status:
            if isinstance(status, str):
                status = [
                    status,
                ]

            filters = filters & dynamo_filter(
                attr_name="status",
                filter_action="in",
                filter_value=status,
            )

        return get_all_items(table_id="request", limit=200, filters=filters)
