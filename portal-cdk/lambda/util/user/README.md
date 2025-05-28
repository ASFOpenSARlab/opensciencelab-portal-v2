# User Class Info

The point of this module, is to abstract the [dynamo_db.py](./dynamo_db.py) module for the rest of the code base, and provide easy management of users.

## How it Works

To Create / Init a User:

```python
user = User("my_user")
# It'll have all the attributes set.
# If it's set in the DB, that's loaded.
# If it's not AND in the defaults file, the default is set. Otherwise it's None.
```

To Access or Modify a User's Attributes:

```python
access = user.access
print(access) # ["user"]
user.access.append("admin") # THIS FAILS! You can't modify direct, reassign it instead:
user.access = user.access + ["admin"] # This works, since it reassigns the value.
# The new access is saved in the DB too, nothing else to do.
```

Fun Tricks:

```python
# Prints a Json representation, for easy viewing.
# Also see all the current attributes available (it won't show class methods, JUST validator_map ones).
print(user) # Shows (at time of writing, specific attributes will change):
{
    "access": [
        "user"
    ],
    "some_int_without_default": null,
    "some_int_with_default": 42,
    "random_dict": null
}
```

### Why do I have to reassign access every time?

Because this class works by wrapping around `__setattr__` to know when attributes are changed, it's impossible for the class to know that the list assigned to the value is modified. This is because behind the scenes, you use `__getattr__` to get a POINTER to the list, then you modify the list directly. Since the `__setattr__` is what we use to know when to update the DB, it'd never get called.

- To get around this, I use `frozendict.deepfreeze`. This'll make every list and dict that's a value (included nested) to be immutable. This forces you to reassign the value, and we won't accidentally miss a change.

Other possible options that failed (so others don't make the same mistake):

- You can subclass `user` and `dict`, that includes a `callback` method to tell the class you changed. The problem is if the callback is just `user.save()`, the thing you append to the list never gets verified with the validator.
  - If instead the callback is `user.__setattr__(key, val)`, you'll have a ugly lambda to pass in as the callback and it won't work for any nested objects. The nested object will set itself as the "base" object, and override any data there.
- If you leave it as is without freezing it, You can modify the list directly, but can easily forget to save the user, and thus any changes is lost. If we went this route, I'd want you to ALWAYS have to call .save(), which sort-of defeats the point of abstracting this.

## Different Components

- [dynamo_db.py](./dynamo_db.py): This directly interacts with the DynamoDB table itself. It's in this module since only the module should ever be interacting with it directly. Everything else should use the [User Class](./user.py).
- [user.py](./user.py): This is the main module everything should use to interact with users and their info.
- [validator_map.py](./validator_map.py): This holds all the attributes the [User Class](./user.py) is allowed to have, along with how to validate that attribute. You can use classic (`list`, `str`, `int`, ...) to validate, or write your own in the [validators.py](./validators.py) file.
- [validators.py](./validators.py): This holds all the custom validators you can use in the [validator_map.py](./validator_map.py) file. You can cast/transform values here, or raise a ValueError if they're not what you expect.

## Updating The [validator_map.py](./validator_map.py)

### Adding a NEW validator / attribute key

> [!NOTE]
> With the validator_map `keys`, you CAN'T use `-` or any other character that isn't allowed in attributes! (Think obj.attr_name, NOT obj.attr-name or obj.@attr, etc.).

This is luckily simple.

1) Add the key to the [validator_map.py](./validator_map.py) dict.
2) If you want it to have a DIFFERENT default than `None`, add the same key to [defaults.py](./defaults.py) with it's val as that default.
3) If you want it to have CUSTOM validation logic, add a function to [validators.py](./validators.py) that takes the value and returns the value if valid, or raises a ValueError if invalid. Otherwise you can just use `str`, `int`, `list`, etc as the value in the [validator_map.py](./validator_map.py) dict.

And that's it! Any DB entries that were created before it was added, will have the value set to the default when they're loaded next.

### Modifying an EXISTING validator / attribute key

This is one part I haven't experimented much with

This can be tricky with [validators.py](./validators.py) too. If you have data in the DB, and change a validator: make sure that all the DB entries still pass. You might have to write a quick script to convert any that don't. When the User class next loads that user otherwise, it'll fail the validation check and thus loading.

- This could be a good test to add: For each user, make sure that all user objects load. It'd be tricky when to run this though, if you're running on prod, it'd catch the error too late.
