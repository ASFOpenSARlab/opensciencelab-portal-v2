"""Lab Class to abstract the rest of the code using the database."""

from util.exceptions import LabDoesNotExist
from util.labs import LAB_CONFIGS
from util.dynamo_db import get_item, create_item
from objs.base_db_table import Table

from .defaults import defaults
from .validator_map import validator_map

LAB_TABLE_ID = "lab"
LAB_TABLE_KEY = "labname"


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
        db_info = get_item(self.labname, key_name=LAB_TABLE_KEY, table_id=LAB_TABLE_ID)

        # Error if the lab isn't valid
        if not db_info and self.labname not in LAB_CONFIGS:
            raise LabDoesNotExist(
                f"Lab {self.labname} does not exist.",
            )

        # Create item in the DB, if it doesn't exist, and it's in LAB_CONFIGS
        if not db_info:
            create_item(
                self.labname,
                defaults,
                key_name=LAB_TABLE_KEY,
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
