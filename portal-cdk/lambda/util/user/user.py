
import json
from copy import deepcopy

from util.exceptions import DbError
from util.dynamo_db import get_item, create_item, update_item, delete_item, get_all_items

from .defaults import defaults
from .validator_map import validator_map, validate


def _callback_object_wrapper(_object, callback):
    if isinstance(_object, list):
        return CallbackList(_object, callback=callback)
    else:
        return _object


class CallbackList(list):
    """
    A list that calls a function when an item is added.
    """
    def __init__(self, data, callback=None):
        super().__init__(data)
        self.callback = callback

    def append(self, item):
        item = _callback_object_wrapper(item, self.callback)
        super().append(item)
        if self.callback:
            self.callback()

    def extend(self, items):
        for item in items:
            item = _callback_object_wrapper(item, self.callback)
        super().extend(items)
        if self.callback:
            self.callback()


class User():

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
                self.__setattr__(key, db_info[key])
            else:
                self.__setattr__(key, None)

    def __setattr__(self, key, value):
        if key not in validator_map:
            raise DbError(
                f"Key '{key}' not in validator_map for user {self.username}.",
                error_code=500,
                extra_info=self.db,
            )
        ## Set the Value:
        if value is None:
            if key in defaults:
                super().__setattr__(key, defaults[key])
            else:
                # This is separated, so it doesn't pass through 'validate':
                super().__setattr__(key, None)
        else:
            super().__setattr__(key, validate(key, value))
        ## Cast it to a smart list/dict if needed:
        super().__setattr__(
            key,
            _callback_object_wrapper(self.__getattribute__(key), callback=self._save)
        )
        ## Update the DB:
        update_item(self.username, {key: self.__getattribute__(key)})

    def __str__(self):
        """
        What to display if you print this object.
        """
        return json.dumps(dict(self), indent=4, default=str)

    def __iter__(self):
        """
        Used when casting to a dict, what keys to show.
        """
        for key in validator_map:
            yield key, self.__getattribute__(key)

    def _save(self):
        """
        Saves the current state of the user to the DB.
        """
        update_item(self.username, dict(self))

if __name__ == "__main__":
    # delete_item("cjshowalter")  # Clean up for testing.
    me = User("cjshowalter")
    me.access.append("admin")
    print(type(me.access))
    print(me)
    print(get_all_items())

