"""User Class to abstract the rest of the code using the database."""

import datetime
from typing import Any

from util.exceptions import DbError, CognitoError, UserNotFound, LabDoesNotExist
from util.cognito import delete_user_from_user_pool
from util.labs import LAB_CONFIGS
from util.dynamo_db import (
    get_item,
    create_item,
    delete_item,
    dynamo_filter,
    get_all_items,
    combine_all_dynamo_filters,
    get_items_lazy,
)
from data import DATE_F
from objs.base_db_table import Table
from .defaults import defaults
from .validator_map import validator_map

USER_TABLE_ID = "user"
USER_TABLE_KEY = "username"


def create_lab_structure(
    lab_profiles: list[str],
    **kwargs,
) -> dict[str, Any]:
    return {
        "lab_profiles": lab_profiles,
    }


class User(Table):
    def __init__(self, username: str, create_if_missing: bool = True):
        # Create a User Table
        super().__init__(
            unique_key_value=username,
            unique_key_name=USER_TABLE_KEY,
            table_id=USER_TABLE_ID,
            defaults=defaults,
            validator_map=validator_map,
        )

        super().__setattr__(USER_TABLE_KEY, username)

        ## Apply anything in the DB:
        db_info = get_item(key={USER_TABLE_KEY: self.username}, table_id=USER_TABLE_ID)

        if not db_info and not create_if_missing:
            raise UserNotFound(
                f"User {self.username} does not exist and was not created",
            )

        ## If it doesn't exist, create it with the defaults:
        if not db_info:
            create_item(
                key={USER_TABLE_KEY: self.username},
                item=defaults,
                table_id=USER_TABLE_ID,
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

    def update_last_cookie_assignment(self) -> None:
        self.last_cookie_assignment = datetime.datetime.now().strftime(DATE_F)

    # Lab manipulation methods
    def set_labs(self, formatted_labs: dict) -> None:
        self.labs = formatted_labs

    def add_lab(self, **kwargs) -> None:
        new_lab_list = {}
        for lab in self.labs.keys():
            new_lab_list[lab] = self.labs[lab]

        new_lab_list[kwargs["lab_short_name"]] = create_lab_structure(**kwargs)

        self.labs = new_lab_list

    def remove_lab(self, lab_short_name: str) -> None:
        new_lab_list = {}
        for lab in self.labs.keys():
            if lab != lab_short_name:
                new_lab_list[lab] = self.labs[lab]
        self.labs = new_lab_list

    def get_lab_access(self) -> dict:
        """Returns ALL labs the user has access to."""
        return filter_lab_access(self)

    def is_authorized_lab(self, lab_short_name: str) -> bool:
        """Check if the user has access to a specific lab."""
        if self.is_admin():
            return True
        return lab_short_name in self.labs

    # Convenience methods
    def is_admin(self) -> bool:
        return "admin" in self.access

    def is_lab_manager(self, lab) -> bool:
        return self.username in lab.managers and "lab_manager" in self.access

    def remove_user(self) -> bool:
        # Delete user from Cognito
        if not delete_user_from_user_pool(self.username):
            raise CognitoError(f"Could not delete Cognito user {self.username}")

        # Delete item from dynamodb
        delete_item(key={USER_TABLE_KEY: self.username}, table_id=USER_TABLE_ID)

        # ensure item is deleted
        if get_item(key={USER_TABLE_KEY: self.username}, table_id=USER_TABLE_ID):
            raise DbError(f"Could not delete db user {self.username}")

        return True

    def get_requests(self, status: str | list | None = None):
        filters = dynamo_filter(
            attr_name=USER_TABLE_KEY, filter_value=self.username, filter_action="eq"
        )

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

    def use_token(self, labname, token_value):
        # Can't append directly, copy + append
        current_usage = list(self.token_usage)
        current_usage.append(
            {
                "labname": labname,
                "token": token_value,
                "apply_date": datetime.datetime.now().strftime(DATE_F),
            }
        )
        self.token_usage = current_usage

    def check_used_token(self, token_value):
        for token in self.token_usage:
            if token["token"] == token_value:
                return True
        return False

    def grant_access_role(self, access_role: str):
        current_roles: set = set(self.access)
        current_roles.add(access_role)
        self.access = current_roles

    def revoke_access_role(self, access_role: str):
        current_roles: set = set(self.access)
        current_roles.remove(access_role)
        self.access = current_roles


def _can_user_see_lab(user: User, lab) -> bool:
    if user.is_admin():
        return True
    # user is not admin
    if lab.short_lab_name not in user.labs and lab.accessibility == "private":
        return False
    # user has access, or lab is protected or public
    return True


def _can_user_access_lab(user: User, lab) -> bool:
    if user.country_code in lab.ip_country_status["prohibited"]:
        return False
    # user not georestricted
    if lab.short_lab_name not in user.labs:
        return False
    # user has access
    return True


# returns labs filtered by user access
def filter_lab_access(user: User) -> dict:
    # Dynamically create can_user_x flags
    user_lab_permissions = {}
    for labname, lab_info in LAB_CONFIGS.items():
        user_lab_permissions[labname] = {
            "can_user_see_lab": _can_user_see_lab(user, lab_info),
            "can_user_access_lab": _can_user_access_lab(user, lab_info),
        }
        ## ONLY if user has access to the lab, add their lab info
        # (can_user_*_lab must exist for EVERY lab)
        if labname in user.labs:
            # if user has access, add user.labs access info
            user_lab_permissions[labname] |= user.labs[labname]

    return {
        "viewable_labs_config": {
            labname: LAB_CONFIGS[labname]
            for labname in user_lab_permissions.keys()
            if user_lab_permissions[labname]["can_user_see_lab"]
        },
        "lab_access": {
            labname: access
            for labname, access in user_lab_permissions.items()
            if user_lab_permissions[labname]["can_user_see_lab"]
        },
    }


def user_email_filters(username_filter, email_filter):
    # Combine all filters
    filters = []
    if username_filter:
        filters.append(
            dynamo_filter(attr_name=USER_TABLE_KEY, filter_value=username_filter)
        )
    if email_filter:
        filters.append(dynamo_filter(attr_name="email", filter_value=email_filter))

    return combine_all_dynamo_filters(filters)


# Returns a list of users usernames that have access to a given lab
def get_users_with_lab(
    lab_short_name: str,
    limit: int | None = None,
    username_filter: str | None = None,
    email_filter: str | None = None,
) -> list[dict]:
    # Check if lab exists
    if lab_short_name not in LAB_CONFIGS:
        raise LabDoesNotExist(message=f'"{lab_short_name}" lab does not exist')

    # combine filters
    exist_filter = dynamo_filter(
        attr_name=f"labs.{lab_short_name}", filter_action="exists"
    )
    user_email_filter = user_email_filters(username_filter, email_filter)
    filter_expr = combine_all_dynamo_filters([exist_filter, user_email_filter])

    # Get filtered results
    items = get_all_items(USER_TABLE_ID, limit, filters=filter_expr)

    if limit:
        return items[:limit]

    return items

def get_users_with_lab_lazy(
    lab_short_name: str,
    limit: int | None = None,
    username_filter: str | None = None,
    email_filter: str | None = None,
    exclusive_start_key: dict | None = None,
    minimum_results: int | None = None,
    ):
    # Check if lab exists
    if lab_short_name not in LAB_CONFIGS:
        raise LabDoesNotExist(message=f'"{lab_short_name}" lab does not exist')

    # combine filters
    exist_filter = dynamo_filter(
        attr_name=f"labs.{lab_short_name}", filter_action="exists"
    )
    user_email_filter = user_email_filters(username_filter, email_filter)
    filter_expr = combine_all_dynamo_filters([exist_filter, user_email_filter])

    # Get filtered results
    items, lastEvaluatedKey = get_items_lazy(
        USER_TABLE_ID,
        limit,
        filters=filter_expr,
        exclusiveStartKey=exclusive_start_key,
        minimum_results=minimum_results,
        )

    return items, lastEvaluatedKey
