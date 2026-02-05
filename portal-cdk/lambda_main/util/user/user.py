"""User Class to abstract the rest of the code using the database."""

import json
import datetime
import frozendict
from typing import Any
from util.exceptions import DbError, CognitoError, UserNotFound, LabDoesNotExist
from util.cognito import delete_user_from_user_pool
from util.labs import LABS

from ..dynamo_db import (
    get_item,
    create_item,
    update_item,
    delete_item,
    dynamo_filter,
    get_all_items,
    combine_all_dynamo_filters,
)
from .defaults import defaults
from .validator_map import validator_map, validate

USER_TABLE_ID = "user"
USER_TABLE_KEY = "username"


def create_lab_structure(
    lab_profiles: list[str],
    time_quota,
    lab_country_status: str,
    **kwargs,
) -> dict[str, Any]:
    return {
        "lab_profiles": lab_profiles,
        "time_quota": time_quota,
        "lab_country_status": lab_country_status,
    }


class User:
    def __init__(self, username: str, create_if_missing: bool = True):
        ## Using super to avoid setattr validation. 'username'
        #  should NOT be modified like the other attributes.
        super().__setattr__(USER_TABLE_KEY, username)

        ## Apply anything in the DB:
        db_info = get_item(
            self.username, key_name=USER_TABLE_KEY, table_name=USER_TABLE_ID
        )

        if not db_info and not create_if_missing:
            raise UserNotFound(
                f"User {self.username} does not exist and was not created",
            )

        ## If it doesn't exist, create it with the defaults:
        if not db_info:
            create_item(
                self.username,
                defaults,
                key_name=USER_TABLE_KEY,
                table_name=USER_TABLE_ID,
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

    def __setattr__(self, key, value, _save=True):
        # If it's already that value, do nothing:
        if hasattr(self, key) and self.__getattribute__(key) == value:
            return
        # NOTE: If you use self.__setattr__ here, it will be infinite recursion.
        if key not in validator_map:
            raise DbError(
                f"Key '{key}' not in validator_map for user {self.username}.",
                error_code=500,
                extra_info=dict(self),
            )
        ## Set the Value (if key is the default or None, don't do validation):
        if value is None or self.is_default(key, value):
            # If the val is None AND in defaults, change to default:
            value = defaults[key] if key in defaults else None
            super().__setattr__(key, value)
        else:
            super().__setattr__(key, validate(key, value))
        # Update value, in-case 'validate' or defaults changed it:
        value = self.__getattribute__(key)
        ## Freeze any lists/dicts inside it, so they can't be modified directly:
        super().__setattr__(key, frozendict.deepfreeze(value))
        ## Update the DB:
        if _save:
            update_item(
                self.username,
                updates={key: value},
                key_name=USER_TABLE_KEY,
                table_name=USER_TABLE_ID,
            )

    def __str__(self):
        """What to display if you print this object."""
        return json.dumps(dict(self), indent=4, default=str)

    def __iter__(self):
        """Used when casting to a dict, what keys to show."""
        yield USER_TABLE_KEY, self.username
        for key in validator_map:
            yield key, self.__getattribute__(key)

    def is_default(self, key, value) -> bool:
        """Returns if the value is the default for the key."""
        default_val = defaults.get(key, None)
        return value == default_val

    def update_last_cookie_assignment(self) -> None:
        self.last_cookie_assignment = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

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

    def remove_user(self) -> bool:
        # Delete user from Cognito
        if not delete_user_from_user_pool(self.username):
            raise CognitoError(f"Could not delete Cognito user {self.username}")

        # Delete item from dynamodb
        delete_item(self.username, key_name=USER_TABLE_KEY, table_name=USER_TABLE_ID)

        # ensure item is deleted
        if get_item(self.username, key_name=USER_TABLE_KEY, table_name=USER_TABLE_ID):
            raise DbError(f"Could not delete db user {self.username}")

        return True


def _can_user_see_lab(user: User, lab) -> bool:
    if user.is_admin():
        return True
    # user is not admin
    if lab.short_lab_name not in user.labs and lab.accessibility == "private":
        return False
    # user has access, or lab is protected or public
    return True


def _can_user_access_lab(user: User, lab) -> bool:
    if user.is_admin():
        return True
    # user is not admin
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
    for labname, lab_info in LABS.items():
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
            labname: LABS[labname]
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
    if lab_short_name not in LABS:
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
