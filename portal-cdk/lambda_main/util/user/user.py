"""User Class to abstract the rest of the code using the database."""

import json
import datetime
import frozendict
from typing import Any

from util.exceptions import DbError, CognitoError, UserCreationError
from util.cognito import delete_user_from_user_pool
from util.labs import all_labs, LabAccessInfo, BaseLab

from .dynamo_db import get_item, create_item, update_item, delete_item
from .defaults import defaults
from .validator_map import validator_map, validate


def filter_lab_access(
    is_admin: bool, all_labs_in: dict[str, BaseLab], labs: dict
) -> list[LabAccessInfo]:
    lab_access_info: list[LabAccessInfo] = []
    if is_admin:
        # Admin access to all labs
        for labname in all_labs_in:
            lab_access_info.append(
                LabAccessInfo(
                    lab=all_labs_in[labname],
                    can_user_access_lab=True,
                    can_user_see_lab_card=True,
                )
            )
    else:
        # Determine access from self.labs
        for labname in all_labs_in:
            shortname = all_labs_in[labname].short_lab_name
            if shortname in labs:
                can_user_access_lab = labs[shortname]["can_user_see_lab_card"]
                can_user_see_lab_card = labs[shortname]["can_user_see_lab_card"]
                lab_access_info.append(
                    LabAccessInfo(
                        lab=all_labs_in[labname],
                        can_user_access_lab=can_user_access_lab,
                        can_user_see_lab_card=can_user_see_lab_card,
                    )
                )
    return lab_access_info


def create_lab_structure(
    lab_profiles: list[str],
    time_quota,
    lab_country_status: str,
    can_user_access_lab: bool,
    can_user_see_lab_card: bool,
    **kwargs,
) -> dict[str, Any]:
    return {
        "lab_profiles": lab_profiles,
        "time_quota": time_quota,
        "lab_country_status": lab_country_status,
        "can_user_access_lab": can_user_access_lab,
        "can_user_see_lab_card": can_user_see_lab_card,
    }


class User:
    def __init__(self, username: str, create_if_missing: bool = True):
        ## Using super to avoid setattr validation. 'username'
        #  should NOT be modified like the other attributes.
        super().__setattr__("username", username)

        ## Apply anything in the DB:
        db_info = get_item(self.username)

        if not db_info and not create_if_missing:
            raise UserCreationError(
                f"User {self.username} does not exist and was not created"
            )

        ## If it doesn't exist, create it with the defaults:
        if not db_info:
            create_item(self.username, defaults)
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
            update_item(self.username, {key: value})

    def __str__(self):
        """What to display if you print this object."""
        return json.dumps(dict(self), indent=4, default=str)

    def __iter__(self):
        """Used when casting to a dict, what keys to show."""
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

    def get_lab_access(self) -> list[LabAccessInfo]:
        return filter_lab_access(
            is_admin=self.is_admin(), all_labs_in=all_labs, labs=self.labs
        )

    # Convenience methods
    def is_admin(self) -> bool:
        if "admin" in self.access:
            return True
        return False

    def remove_user(self) -> bool:
        # Delete user from Cognito
        if not delete_user_from_user_pool(self.username):
            raise CognitoError(f"Could not delete Cognito user {self.username}")

        # Delete item from dynamodb
        delete_item(self.username)

        # ensure item is deleted
        if get_item(self.username):
            raise DbError(f"Could not delete db user {self.username}")

        return True
