import json
import sqlite3
import os
import boto3
import argparse
import pathlib

_DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE = None, None, None

# Cognito Client
cog_client = boto3.client("cognito-idp", region_name="us-west-2")

# Get cmd line args
parser = argparse.ArgumentParser(description="Migrate users from OSL Portal v1 to v2")
_ = parser.add_argument(
    "-c",
    "--cognito",
    dest="cognito",
    action="store_true",
    help="Create cognito accounts for all users",
)
_ = parser.add_argument(
    "-t",
    "--dynamo-table-name",
    dest="dynamo_table",
    type=str,
    required=True,
    help="The DynamoDB table name for the migration destination",
)
_ = parser.add_argument(
    "-p",
    "--user-pool-id",
    dest="user_pool_id",
    type=str,
    required=True,
    help="The Cognito User Pool ID for the migration destination",
)
_ = parser.add_argument(
    "-w",
    "--active-window-start",
    dest="active_window_start",
    type=int,
    required=True,
    help="The number of months in the past to start the 'active user' migration window",
)
_ = parser.add_argument(
    "-u",
    "--user-database-path",
    dest="user_database_path",
    default=pathlib.Path("/home/ec2-user/code/services/srv/useretc/db/useretc.db"),
    type=pathlib.Path,
    help="The POSIX file path of the user access database",
)
_ = parser.add_argument(
    "-a",
    "--auth-database-path",
    dest="auth_database_path",
    default=pathlib.Path(
        "/home/ec2-user/code/services/srv/portal/jupyterhub/jupyterhub.sqlite"
    ),
    type=pathlib.Path,
    help="The POSIX file path of the nativeauthenticator database",
)
args = parser.parse_args()


def _get_dynamo():
    """
    Lazy load all DynamoDB stuff since it takes forever the first time.
    """
    global _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE  # pylint: disable=global-statement
    region = os.getenv("STACK_REGION", "us-west-2")
    if not _DYNAMO_CLIENT:
        _DYNAMO_CLIENT = boto3.client("dynamodb", region_name=region)
    if not _DYNAMO_DB:
        _DYNAMO_DB = boto3.resource("dynamodb", region_name=region)
    if not _DYNAMO_TABLE:
        _DYNAMO_TABLE = _DYNAMO_DB.Table(args.dynamo_table)
    return _DYNAMO_CLIENT, _DYNAMO_DB, _DYNAMO_TABLE


def create_item(item: dict) -> bool:
    """
    Creates an item in the DB.
    """
    _client, _db, table = _get_dynamo()
    # "Cast" to a plain dict, so it can be serialized to JSON.
    item = json.loads(json.dumps(item, default=str))
    RESTRICTED_KEYS = []
    for restricted_key in RESTRICTED_KEYS:
        if restricted_key in item:
            raise ValueError(
                f"Can't set '{restricted_key}', that's one we set automatically and WILL get overridden."
            )
    table.put_item(Item=item)
    return True


ALL_SQL = f"""
SELECT
   t1.name as username, 
   t1.admin as is_admin,
   ( select country_code
     from   useretc.geolocation
     where  username = t1.name
     order  by timestamp desc 
     LIMIT 1
   ) as country_code,
   t1.created as created_at, 
   t2.email,
   ( select ip_address 
     from   useretc.geolocation
     where  username = t1.name
     order  by timestamp desc 
     LIMIT 1
   ) as ip_address,
   FALSE as is_locked, --???
   ( select timestamp 
     from   useretc.geolocation
     where  username = t1.name
     order  by timestamp desc 
     LIMIT 1
   ) as last_cookie_assignment,
   t1.last_activity as last_update,

   -- user profile information
   COAL(p1.country_of_residence) as "profile.country_of_residence",
   COAL(p1.faculty_member_affliated_with_university) as "profile.faculty_member_affliated_with_university",
   COAL(p1.graduate_student_affliated_with_university) as "profile.graduate_student_affliated_with_university",
   COAL(p1.is_affliated_with_nasa_research) as "profile.is_affiliated_with_nasa",
   COAL(p1.is_affliated_with_gov_research) as "profile.is_affiliated_with_us_gov_research",
   COAL(p1.is_affliated_with_isro_research) as "profile.is_affliated_with_isro_research",
   COAL(p1.is_affliated_with_university) as "profile.is_affliated_with_university",
   COAL(p1.pi_affliated_with_nasa_research_email) as "profile.pi_affliated_with_nasa_research_email",
   COAL(p1.research_member_affliated_with_university) as "profile.research_member_affliated_with_university",
   COAL(p1.user_affliated_with_gov_research_email) as "profile.user_affliated_with_gov_research_email",
   COAL(p1.user_affliated_with_isro_research_email) as "profile.user_affliated_with_isro_research_email",
   COAL(p1.user_affliated_with_nasa_research_email) as "profile.user_affliated_with_nasa_research_email",
   --p1.user_or_pi_nasa_email as "profile.user_or_pi_nasa_email",

   p1.force_update as require_profile_update,
   0 as "_rec_counter"

FROM
   users AS t1
INNER JOIN
   users_info AS t2 ON t1.name == t2.username,
   useretc.profile AS p1 ON p1.username == t1.name
WHERE
   -- t1.name = 'dgpalmieri' and
   -- User last logged in within the last 12 months
   t1.last_activity > date(current_date, '-{args.active_window_start} months') AND

   -- Filter users out who created and quickly abandoned accounts
   (
       -- User access there account more than 1 day after creation
       t1.last_activity > date(t1.created, '+1 day') OR
       -- OR the user created their account in the last month
       t1.created > date(current_date, '-1 month')
   ) AND

   -- require has_2fa & authorize for accounts NOT created in the last month
   (
      t1.created > date(current_date, '-1 month') OR
      (
          has_2fa = 1 AND
          is_authorized = 1
      )
   )
ORDER by t1.last_activity ASC;
"""

ACCESS_SQL = r"""
WITH 
        wildcard AS (
                /*
                 * Wildcard * "default" usernames need to be applied to all usernames in the lab.
                 * If there is a wildcard present, get the lab and profiles.
                 */
                SELECT
                        lab_short_name,
                        lab_profiles
                FROM access
                WHERE username = '*'
                GROUP BY lab_short_name, username
        ),
        consolidated AS (
                SELECT 
                        access.lab_short_name, 
                        access.username, 
                        access.lab_profiles
                FROM access
                WHERE 
                        /*
                         * IF the special !! is found anywhere in the access sheet for the lab, the whole lab is disregarded.
                         */
                        lab_short_name NOT IN (
                                SELECT a.lab_short_name
                                FROM access AS a 
                                WHERE a.username LIKE '!!%'
                        )
                        /* 
                         * USERNAME that starts with - or _ are used as either placeholders or something not to be used.
                         * The Access sheet also has blanks '' that we don't need.
                         */
                        AND (
                                username NOT LIKE '\_%' ESCAPE '\'
                                AND username NOT LIKE '-%'
                                AND username NOT LIKE ''
                        )
                        /*
                         * Wildcard "Default" * usernames are meaningless in Portal v2
                         */
                        AND (
                                username <> "*" 
                        AND username <> "!*"
                        )
                GROUP BY lab_short_name, username
                HAVING
                        /*
                        * The not ! username means to block the user from the lab. So disregard all instances of the username in the lab. 
                        */
                        username NOT LIKE '!%'
                ORDER BY lab_short_name, username
        )
SELECT
        consolidated.lab_short_name AS lab_short_name,
        consolidated.username AS username,
        /*
        * Select all concated lab profiles, the wildcard default AND also grouped by lab and username, trimmed of whitespace and extra commmas, replacing NULL with " ".
        * A registered Python function "REMOVE_NEAGTED" is used to remove negated (!) profiles. 
        */
        REMOVE_NEGATED(
        trim(
            trim(
                group_concat(
                    coalesce(consolidated.lab_profiles, " ") || "," || coalesce(wildcard.lab_profiles, " "),
                    ","
                )
            ),
        ",")
    ) AS lab_profiles
FROM consolidated
        /*
         * Since all rows in a lab need the defaults, left join only by the lab name.
         */
        LEFT JOIN wildcard
                ON wildcard.lab_short_name = consolidated.lab_short_name
WHERE consolidated.username == ?
GROUP BY consolidated.lab_short_name, consolidated.username
"""


# Define custom sql function
def remove_negated(profiles: str) -> str:
    # Split profiles into a list
    list_profiles: list = profiles.split(",")

    # Get all profiles that start with !
    exclaim_profiles = set(str(u) for u in list_profiles if str(u).startswith("!"))

    # Get all profiles that would be negated by it's conjugate
    unexclaim_profiles = set(u.lstrip("!") for u in exclaim_profiles)

    # Get the full list of profiles to be deleted
    profiles_to_delete = list(exclaim_profiles | unexclaim_profiles)

    # Find all profiles in the original list that are not removed
    usable_profiles = [p for p in list_profiles if p not in profiles_to_delete]

    # Return comma seperated
    return ",".join(usable_profiles)


# Make sure some Python values behave nicely with SQL
# Name taken after the SQL function COALESCE
def coal(user_profile_value: str) -> str:
    if user_profile_value is None:
        user_profile_value = ""

    return user_profile_value


# Connect to DBS
db = sqlite3.connect(f"file:{args.auth_database_path}?mode=ro", uri=True)
db.row_factory = sqlite3.Row  # Enable column fetching

db.create_function("REMOVE_NEGATED", 1, remove_negated)
db.create_function("COAL", 1, coal)

cur = db.cursor()

# Join other DB's
_ = cur.execute(f"ATTACH DATABASE 'file:{args.user_database_path}?mode=ro' AS useretc")

####
_ = cur.execute(ALL_SQL)
rows = [row for row in cur.fetchall()]

active_labs = [
    "smce-prod-opensarlab",
    "smce-test-opensarlab",
    "azdwr-prod-opensarlab",
    "avo-prod",
    "geos636-2025",
]


def migrate_users():
    for row in rows:
        export_object = dict(row)
        cur.execute(ACCESS_SQL, (export_object["username"],))

        labs = [dict(lab) for lab in cur.fetchall()]
        export_object["labs"] = labs

        crafted_export = {
            "username": export_object["username"],
            "access": ["user", "admin"] if export_object["is_admin"] == 1 else ["user"],
            "country_code": export_object["country_code"],
            "created_at": export_object["created_at"],
            "email": export_object["email"],
            "ip_address": export_object["ip_address"],
            "is_locked": export_object["is_locked"] == 1,
            "labs": {
                entry["lab_short_name"]: {
                    "lab_profiles": []
                    if entry["lab_profiles"] is None or entry["lab_profiles"] == ""
                    else [n.strip() for n in entry["lab_profiles"].split(",")]
                }
                for entry in export_object["labs"]
                if entry["lab_short_name"] in active_labs
            },
            "last_cookie_assignment": export_object["last_cookie_assignment"],
            "last_update": export_object["last_update"],
            "profile": {
                "country_of_residence": export_object.get(
                    "profile.country_of_residence", ""
                ),
                "faculty_member_affliated_with_university": export_object.get(
                    "profile.faculty_member_affliated_with_university", "No"
                )
                == "Yes",
                "graduate_student_affliated_with_university": export_object.get(
                    "profile.graduate_student_affliated_with_university", "No"
                )
                == "Yes",
                "is_affiliated_with_nasa": export_object.get(
                    "profile.is_affiliated_with_nasa", ""
                ).lower()
                or None,
                "is_affiliated_with_us_gov_research": export_object.get(
                    "profile.is_affiliated_with_us_gov_research", ""
                ).lower(),
                "is_affliated_with_isro_research": export_object.get(
                    "profile.is_affliated_with_isro_research", ""
                ).lower(),
                "is_affliated_with_university": export_object.get(
                    "profile.is_affliated_with_university", ""
                ).lower(),
                "pi_affliated_with_nasa_research_email": export_object.get(
                    "profile.pi_affliated_with_nasa_research_email", ""
                ).lower(),
                "research_member_affliated_with_university": export_object.get(
                    "profile.research_member_affliated_with_university", "No"
                )
                == "Yes",
                "user_affliated_with_gov_research_email": export_object.get(
                    "profile.user_affliated_with_gov_research_email", ""
                ).lower(),
                "user_affliated_with_isro_research_email": export_object.get(
                    "profile.user_affliated_with_isro_research_email", ""
                ).lower(),
                "user_affliated_with_nasa_research_email": export_object.get(
                    "profile.user_affliated_with_nasa_research_email", ""
                ).lower(),
                "user_or_pi_nasa_email": "none",
            },
            "require_profile_update": True
            if export_object.get("require_profile_update", 1) == 1
            else False,
            "_rec_counter": export_object["_rec_counter"],
        }

        try:
            _ = create_item(crafted_export)
            print(f"Created user {crafted_export['username']} in DynamoDB")
        except Exception as e:
            print(
                f"EXCEPTION THROWN \n {e} \n for username {crafted_export['username']}"
            )

        if args.cognito:
            try:
                cog_client.admin_create_user(
                    UserPoolId=args.user_pool_id,
                    Username=crafted_export["username"],
                    UserAttributes=[
                        {"Name": "email", "Value": crafted_export["email"]}
                    ],
                )
                print(f"Created user {crafted_export['username']} in Cognito")
            except Exception as e:
                print(
                    f"EXCEPTION THROWN \n {e} \n for username {crafted_export['username']}"
                )


if __name__ == "__main__":
    migrate_users()
