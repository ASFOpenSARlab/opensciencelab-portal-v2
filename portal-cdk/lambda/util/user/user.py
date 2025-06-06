"""User Class to abstract the rest of the code using the database."""

import json
import datetime

import frozendict

from util.exceptions import DbError

from .dynamo_db import get_item, create_item, update_item
from .defaults import defaults
from .validator_map import validator_map, validate


class User:
    def __init__(self, username: str):
        ## Using super to avoid setattr validation. 'username'
        #  should NOT be modified like the other attributes.
        super().__setattr__("username", username)

        ## Apply anything in the DB:
        db_info = get_item(self.username)
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
        self.last_cookie_assignment = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
