
import datetime
from dataclasses import dataclass

# from frozenlist import FrozenList
# from frozendict import frozendict

from .dynamo_db import get_item, create_item, update_item, get_all_items


class CallbackList(list):
    """
    A list that calls a function when an item is set.
    """
    def __init__(self, callback, iterable=None):
        if iterable is None:
            iterable = []
        self.callback = callback
        super().__init__(i for i in iterable)

    # def __setitem__(self, index, item):
    #     super().__setitem__(index, item)
    #     self.callback()

    def append(self, item):
        super().append(item)
        self.callback()

    # def extend(self, other):
    #     super().extend(other)
    #     self.callback()

@dataclass
class User(dict):
    """
    User class that loads and saves to the DB.
    """
    def __init__(self, username):
        super().__init__()
        self.username = username
        user_info = get_item(self.username)
        # If user doesn't exist in db:
        if not user_info:
            user_info = create_item(self.username, {
                "access": ["user"],
            })
        # Copy all of the items to THIS dict:
        for key, val in user_info.items():
            ## Load the rest:
            self.__setitem__(key, val)

    def __setitem__(self, key, value):
        """
        Set an item in the DB and the class.
        """
        # Whitelist of Items NOT to load into dict:
        if key in ["username", "created-at", "last-update"]:
            return

        # If it's a list or dict, cast it to our callback version:
        if isinstance(value, list):
            value = CallbackList(self.save, value)

        update_item(self.username, {
            key: value,
        })
        super().__setitem__(key, value)

    def grant_lab_access(self, lab):

        self["labs"].append(lab)
        self.save()

    def save(self):
        """
        Save the user to the DB.
        """
        for key, val in self.items():
            update_item(self.username, {
                key: val,
            })

    # def __del__(self):
    #     raise RuntimeError("Deleting from UserClass not (yet?) supported.")

    def reset_mfa(self):
        pass

if __name__ == "__main__":

    me = User("cjshowalter")


    print(me)
    print(me["access"])
    me["access"].append("admin")
    me["access"] = me["access"] + ["admin"]
    print(me["access"])
    
    print(get_all_items())

