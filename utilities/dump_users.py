import json
import sqlite3

USER_ETC_DB = "/home/ec2-user/code/services/srv/useretc/db/useretc.db"
JUPYTER_HUB_DB = "/home/ec2-user/code/services/srv/portal/jupyterhub/jupyterhub.sqlite"
EXPORT_ACTIVITY_CUTOFF_MONTHS = 13

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
   p1.country_of_residence as "profile.country_of_residence",
   p1.faculty_member_affliated_with_university as "profile.faculty_member_affliated_with_university",
   p1.graduate_student_affliated_with_university as "profile.graduate_student_affliated_with_university",
   p1.is_affliated_with_nasa_research as "profile.is_affiliated_with_nasa",
   p1.is_affliated_with_gov_research as "profile.is_affiliated_with_us_gov_research",
   p1.is_affliated_with_isro_research as "profile.is_affliated_with_isro_research",
   p1.is_affliated_with_university as "profile.is_affliated_with_university",
   p1.pi_affliated_with_nasa_research_email as "profile.pi_affliated_with_nasa_research_email",
   p1.research_member_affliated_with_university as "profile.research_member_affliated_with_university",
   p1.user_affliated_with_gov_research_email as "profile.user_affliated_with_gov_research_email",
   p1.user_affliated_with_isro_research_email as "profile.user_affliated_with_isro_research_email",
   p1.user_affliated_with_nasa_research_email as "profile.user_affliated_with_nasa_research_email",
   --p1.user_or_pi_nasa_email as "profile.user_or_pi_nasa_email",

   p1.force_update as require_profile_update,
   0 as "_rec_counter"

FROM
   users AS t1
INNER JOIN
   users_info AS t2 ON t1.name == t2.username,
   useretc.profile AS p1 ON p1.username == t1.name
WHERE
   -- t1.name = 'bbuechle' and
   -- User last logged in within the last 12 months
   t1.last_activity > date(current_date, '-{EXPORT_ACTIVITY_CUTOFF_MONTHS} months') AND

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

ACCESS_SQL = """
select 
   lab_short_name,
   username,
   lab_profiles 
from 
   useretc.access
where
   username = ?;
"""

# Connect to DBS
db = sqlite3.connect(f"file:{JUPYTER_HUB_DB}?mode=ro", uri=True)
db.row_factory = sqlite3.Row  # Enable column fetching
cur = db.cursor()

# Join other DB's
_ = cur.execute(f"ATTACH DATABASE 'file:{USER_ETC_DB}?mode=ro' AS useretc")

####
_ = cur.execute(ALL_SQL)
rows = [row for row in cur.fetchall()]

for row in rows:
    export_object = dict(row)
    cur.execute(ACCESS_SQL, (export_object["username"],))

    labs = [dict(lab) for lab in cur.fetchall()]
    export_object["labs"] = labs

    crafted_export = {
        "username": {"S": export_object["username"]},
        "access": {"L": [{"S": "user"}, {"S": "admin"}]}
        if export_object["is_admin"] == 1
        else {"L": [{"S": "user"}]},
        "country_code": {"S": export_object["country_code"]},
        "created_at": {"S": export_object["created_at"]},
        "email": {"S": export_object["email"]},
        "ip_address": {"S": export_object["ip_address"]},
        "is_locked": {"BOOL": export_object["is_locked"] == 1},
        "labs": {
            "M": {
                entry["lab_short_name"]: {
                    "M": {
                        "lab_profiles": {
                            "L": []
                            if entry["lab_profiles"] is None
                            or entry["lab_profiles"] == ""
                            else [n.strip() for n in entry["lab_profiles"].split(",")]
                        }
                    }
                }
            }
            for entry in export_object["labs"]
        },
        "last_cookie_assignment": {"S": export_object["last_cookie_assignment"]},
        "last_update": {"S": export_object["last_update"]},
        "profile": {
            "M": {
                "country_of_residence": {
                    "S": export_object["profile.country_of_residence"]
                },
                "faculty_member_affliated_with_university": {
                    "BOOL": export_object[
                        "profile.faculty_member_affliated_with_university"
                    ]
                    == "Yes"
                },
                "graduate_student_affliated_with_university": {
                    "BOOL": export_object[
                        "profile.graduate_student_affliated_with_university"
                    ]
                    == "Yes"
                },
                "is_affiliated_with_nasa": {
                    "S": export_object["profile.is_affiliated_with_nasa"].lower()
                },
                "is_affiliated_with_us_gov_research": {
                    "S": export_object[
                        "profile.is_affiliated_with_us_gov_research"
                    ].lower()
                },
                "is_affliated_with_isro_research": {
                    "S": export_object[
                        "profile.is_affliated_with_isro_research"
                    ].lower()
                },
                "is_affliated_with_university": {
                    "S": export_object["profile.is_affliated_with_university"].lower()
                },
                "pi_affliated_with_nasa_research_email": {
                    "S": export_object[
                        "profile.pi_affliated_with_nasa_research_email"
                    ].lower()
                },
                "research_member_affliated_with_university": {
                    "BOOL": export_object[
                        "profile.research_member_affliated_with_university"
                    ]
                    == "Yes"
                },
                "user_affliated_with_gov_research_email": {
                    "S": export_object[
                        "profile.user_affliated_with_gov_research_email"
                    ].lower()
                },
                "user_affliated_with_isro_research_email": {
                    "S": export_object[
                        "profile.user_affliated_with_isro_research_email"
                    ].lower()
                },
                "user_affliated_with_nasa_research_email": {
                    "S": export_object[
                        "profile.user_affliated_with_nasa_research_email"
                    ].lower()
                },
            }
        },
        "random_dict": {"NULL": True},
        "require_profile_update": {
            "BOOL": True if export_object["require_profile_update"] == 1 else False
        },
        "some_int_without_default": {"NULL": True},
        "_rec_counter": {"N": export_object["_rec_counter"]},
    }

    print(json.dumps(export_object, indent=2))
    print(json.dumps(crafted_export, indent=2))

    break
