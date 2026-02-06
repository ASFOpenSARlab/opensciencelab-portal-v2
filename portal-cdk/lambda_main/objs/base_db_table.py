"""Lab Class to abstract the rest of the code using the database."""

import json
import frozendict

from util.exceptions import DbError
from util.dynamo_db import update_item


class Table:
    def __init__(
        self,
        unique_key_value: str,  # "geos626"
        unique_key_name: str,  # "labname"
        table_id: str,  # "lab"
        defaults: dict | None = None,
        validator_map: dict | None = None,
    ):
        super().__setattr__(
            "validator_map", validator_map if validator_map else {"_rec_counter": int}
        )
        super().__setattr__(
            "defaults",
            defaults if defaults else {"_rec_counter": 1},
        )

        super().__setattr__("unique_key_value", unique_key_value)
        super().__setattr__("unique_key_name", unique_key_name)
        super().__setattr__("table_id", table_id)

        # Set the unique key
        super().__setattr__(unique_key_name, unique_key_value)

    def __setattr__(self, key, value, _save=True):
        # If it's already that value, do nothing:
        if hasattr(self, key) and self.__getattribute__(key) == value:
            return
        # NOTE: If you use self.__setattr__ here, it will be infinite recursion.
        if key not in self.validator_map:
            raise DbError(
                f"Key '{key}' not in validator_map for {self.table_id} {self.unique_key_value}.",
                error_code=500,
                extra_info=dict(self),
            )
        ## Set the Value (if key is the default or None, don't do validation):
        if value is None or self.is_default(key, value):
            # If the val is None AND in defaults, change to default:
            value = self.defaults[key] if key in self.defaults else None
            super().__setattr__(key, value)
        else:
            super().__setattr__(key, self.validate(key, value))
        # Update value, in-case 'validate' or defaults changed it:
        value = self.__getattribute__(key)
        ## Freeze any lists/dicts inside it, so they can't be modified directly:
        super().__setattr__(key, frozendict.deepfreeze(value))
        ## Update the DB:
        if _save:
            update_item(
                self.unique_key_value,
                updates={key: value},
                key_name=self.unique_key_name,
                table_id=self.table_id,
            )

    def __str__(self):
        """What to display if you print this object."""
        return json.dumps(dict(self), indent=4, default=str)

    def __iter__(self):
        """Used when casting to a dict, what keys to show."""
        yield self.unique_key_name, self.unique_key_value
        for key in self.validator_map:
            yield key, self.__getattribute__(key)

    def is_default(self, key, value) -> bool:
        """Returns if the value is the default for the key."""
        default_val = self.defaults.get(key, None)
        return value == default_val

    def validate(self, key, value):
        try:
            return self.validator_map[key](value)
        except ValueError as e:
            raise DbError(f"Invalid value for {key}: {value}. Error: {e}") from e
