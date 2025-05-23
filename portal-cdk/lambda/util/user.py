
import datetime
from dataclasses import dataclass


from collections import UserDict
from .dynamo_db import get_item, create_item, update_item, get_all_items

# class User():

#     access = []
#     def __init__(self, username):
#         self.username = username
#         self.sync()

#     def sync(self):
#         """
#         Syncs the user info to what's in the DB.
#         """
#         # If user doesn't exist in db:
#         user_info = get_item(self.username)
#         if not user_info:
#             user_info = create_item(self.username, {
#                 "access": ["user"],
#             })
#         self.access = user_info["access"]

#     def set_access(self):
#         """
#         Sets the access level of the user.
#         """
#         update_item(self.username, {
#             "access": self.access,
#         })
#         self.sync()
#         return self.access

# if __name__ == "__main__":
#     my_user = User("cjshowalter")
#     # print(my_user["access"])
#     # my_user["access"].append("user")
#     # print(my_user["access"])
#     print(dir(my_user))
#     print(my_user.get_class_attributes())
#     # print(get_all_items())


##################
### OPTION TWO ###
##################
# Using Attributes instead of a dict. Looks like it has the same problem though, where
# it doesn't call __setitem__ when you modify the list directly.

class User():

    def __init__(self, username):
        self.username = username
        self.load()

    def load(self):
        """
        Load the DB info INTO the class.
        """
        # If user doesn't exist in db:
        user_info = get_item(self.username)
        if not user_info:
            user_info = create_item(self.username, {
                "access": ["user"],
            })
        for key, val in user_info.items():
            # Whitelist of Items NOT to load:
            if key in ["username", "created-at", "last-update"]:
                continue
            # Load the rest:
            self.__setattr__(key, val)


    def get_class_attributes(self):
        return {
            name: attr for name, attr in self.__dict__.items()
            if not name.startswith("__") and not callable(attr) and not name in ["username"]
        }

if __name__ == "__main__":
    my_user = User("cjshowalter")
    # print(my_user["access"])
    # my_user["access"].append("user")
    # print(my_user["access"])
    print(dir(my_user))
    print(my_user.get_class_attributes())
    # print(get_all_items())


##################
### OPTION ONE ###
##################

"""
UserDict Option:

For example, adding admin to the list of access params. It'll ONLY work for something like this:

```python
    my_user = User("cjshowalter")
    print(my_user["access"])
    my_user["access"] = ["user", "admin"]
    print(my_user["access"])
    print(dir(my_user))
    print(get_all_items())
```

If we instead switch the 3rd line to:

```python
    my_user = User("cjshowalter")
    print(my_user["access"])
    my_user["access"].append("user")
    print(my_user["access"])
    print(dir(my_user))
    print(get_all_items())
```

This is because this method works by overriding the __setitem__ part of a dict, which is only called with "=".
The second append method, uses __getitem__ to get the pointer to the list, then modifies the list directly. It never needs
to call __setitem__.

BUT the advantage to this method is even if an item isn't currently in the dict, the code can easily add it:

```python
my_user = User("cjshowalter")
my_user["new-feature"] = "pizza" # and just like that, it's in the DB.
```

Two ways I can think of to counter this:
1) Have a `self.save()` method that saves the entire dict to the DB.
2) Have self.__setitem__() check if it's a list or dict, and make it immutable. FORCE you to re-create it.

"""
# @dataclass
# class User(UserDict):
#     """
#     User class that loads and saves to the DB.
#     """
#     def __init__(self, username):
#         super().__init__()
#         self.username = username
#         user_info = get_item(self.username)
#         # If user doesn't exist in db:
#         if not user_info:
#             user_info = create_item(self.username, {
#                 "access": ["user"],
#             })
#         # Copy all of the items to THIS dict:
#         for key, val in user_info.items():
#             ## Load the rest:
#             self.__setitem__(key, val)

#     def __setitem__(self, key, value):
#         """
#         Set an item in the DB and the class.
#         """
#         # Whitelist of Items NOT to load into dict:
#         if key in ["username", "created-at", "last-update"]:
#             return
#         update_item(self.username, {
#             key: value,
#         })
#         super().__setitem__(key, value)

#     # def __del__(self):
#     #     raise RuntimeError("Deleting from UserClass not (yet?) supported.")

