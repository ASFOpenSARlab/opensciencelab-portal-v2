# Cognito User Importing Notes

- [AWS Cognito's Docs on Importing Users](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-using-import-tool.html).

## Basic Steps

- Go to your user pool, then `Users` under `User management`.
- At the bottom, click `Create import job`.
- The job name can be whatever. Create a new IAM role, I normally make the name match the job name, with `-role` after.
- Upload the CSV! (Warnings in the next part).
- Click `Create and start job`. It'll take a few minutes, even with just one user. Once it actually starts, you can watch it's progress in the cloudwatch group it creates.
- (QUESTION!): Looks like the role it automatically creates does NOT get cleaned up afterward. Should we have a step here to delete it afterwards? We can also tweak these steps to only use a generic role we create once through the above steps then too...

## CSV Format

The CSV format looks like this:

```csv
profile,address,birthdate,gender,preferred_username,updated_at,website,picture,phone_number,phone_number_verified,zoneinfo,locale,email,email_verified,given_name,family_name,middle_name,name,nickname,cognito:mfa_enabled,cognito:username
```

All fields MUST exist, but can be blank. For us, the only required fields are [cognito:username, email_verified, email, and cognito:mfa_enabled](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-using-import-tool.html#cognito-user-pools-using-import-tool-formatting-csv-file). You can `email*` stuff with `phone*` too.

So a "minimal" user CSV with the same header as above would look like this, with most fields blank:

```csv
,,,,,,,,,,,,<USERS_EMAIL_HERE>,true,,,,,,TRUE,imported_username
```

### Edge Cases

With ANY job run, there's a link in the summary to see the logs. That should be your best friend if there's any issues.

#### Users outside of regex

Users outside the regex DON'T fail, and will be imported just fine. This means if we want to force username constraints, we have to filter the usernames before importing first.

It also means if we want to "grandfather" in existing usernames, but only be more strict going forward, we can do that too.

#### Duplicate usernames

This one behaves like you expect. If they're in the same file, the first imports, and the second is skipped. Logs also show it as expected.

#### Invalid email address format

More than likely, you didn't edit the `<USERS_EMAIL_HERE>` in the example CSV above.

## Exporting from Portal v1

On the portal v1's EC2, run (in a python shell):

```python
# Create a Curser to run SQL Queries on the DB
import sqlite3
db = sqlite3.connect('file:/home/ec2-user/code/services/srv/portal/jupyterhub/jupyterhub.sqlite?mode=ro', uri=True)
cur = db.cursor()
```

You'll copy-paste this into the python shell in the next step.

```SQL
SELECT 
   t1.name, t1.created, t1.last_activity, t2.email 
FROM 
   users AS t1 
INNER JOIN 
   users_info AS t2 ON t1.name == t2.username 
WHERE 
   -- User last logged in within the last 12 months
   t1.last_activity > date(current_date, '-1 year') AND

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
```

Run the above SQL query in the python shell, to load the data into python:

```python
# Load the Data (SQL is a multi-line string)
cur.execute("""
<SQL QUERY FROM ABOVE>
""")
data = [row for row in cur.fetchall()]
```

Finally save it to a CSV:

```python
import csv
# Get the csv "header" at the beginning of the data list, for the CSV:
data.insert(0, ("users.name", "users.created", "users.last_activity", "users_info.email"))
# Aaand finally save it:
with open("user_db_export.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(data)
```

In IAM, create an access key under your user. (`IAM` > `Users` > You  > `Create access key` > `Command Line interface (CLI)` > `Create`).

Then, on your local machine, run:

```bash
# QUOTES around the variables:
export AWS_ACCESS_KEY_ID="<YOUR_ACCESS_KEY_ID>"
export AWS_SECRET_ACCESS_KEY="<YOUR_SECRET_ACCESS_KEY>"
aws s3 cp ./user_db_export.csv "s3://portal-v1-user-data-export/db-export-($(date +'%Y-%m-%d %H:%M:%S')).csv"
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
```

Then delete the key from your IAM user too. You can now download the CSV from the S3 bucket.

### Get Table Information

Some helpful queries, if we need to expand the DB query above more later on.

```python
# Query for tables
>>> cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
>>> [row[0] for row in cur.fetchall()]
```

```python
# See the fields inside of a table (i.e here, profile)
>>> cur.execute("PRAGMA table_info(profile);")
>>> [row for row in cur.fetchall()]
```
