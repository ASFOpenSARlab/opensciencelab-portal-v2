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

VALID_REQUEST_STATUSES = ["new", "approved", "rejected", "pending", "returned"]
LOCKED_REQUEST_STATUSES = ["approved", "rejected"]
ACTIVE_REQUEST_STATUSES = list(set(VALID_REQUEST_STATUSES).difference(set(LOCKED_REQUEST_STATUSES)))


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

        Don't call directly. Use add_access_request()

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

    def grant_user_access(self, username: str, profiles: list | None = None) -> None:
        """

        Args:
            username: User who should be given access

        """

        from objs.user import User

        # If profiles aren't supplied, use the lab defaults
        if not profiles:
            profiles = self.get_lab_config().default_profiles

        add_user = User(username)

        add_user.add_lab(
            lab_short_name=self.labname,
            lab_profiles=profiles,
            time_quota=None,
            lab_country_status=None,
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

        # Look up the lab access questions
        lab_questions = [z["name"] for z in self.access_request_questions()]

        # Copy in received answers
        answers_dict = {}
        for question in lab_questions:
            answers_dict[question] = answers.get(question)

        # Add user metadata fields:
        ip_address, country_code = get_ip_and_country(current_session.app.current_event)
        answers_dict["submission_ip"] = ip_address
        answers_dict["submission_cc"] = country_code
        answers_dict["submission_date"] = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Grab persistent admin fields from old requests
        for other in ("submission_comment", "submission_reviewer"):
            if other in answers:
                # Supplied with update
                answers_dict[other] = answers[other]
            elif other in req_dict:
                # Pulled from previous record
                answers_dict[other] = req_dict[other]

        # Add answers to the end of the list
        req_dict["answers"].append(answers_dict)

        # Save record
        self._put_access_request(req_dict, username)

    def set_access_request_status(
        self,
        username: str,
        status: str,
        reviewer: str,
        reviewer_comment: str | None = None,
    ):
        """

        Args:
            username: User with an existing access request
            status: New status to update request to
            reviewer: Admin who changed the status
            reviewer_comment: Optional admin comment

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
        if req_dict["status"] == status and not reviewer_comment:
            return

        # Copy & update answers
        req_dict["answers"].append(req_dict["answers"][-1])
        req_dict["answers"][-1]["submission_reviewer"] = reviewer
        if reviewer_comment:
            req_dict["answers"][-1]["submission_comment"] = reviewer_comment

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

    def get_lab_config(self):
        """
        grab a BaseLabConfig() object for the lab
        """
        if self.labname not in LAB_CONFIGS:
            return False

        return LAB_CONFIGS[self.labname]

    def allows_access_request(self) -> bool:
        return len(self.get_lab_config().application_questions) > 0

    def access_request_questions(self) -> dict:
        return self.get_lab_config().application_questions
