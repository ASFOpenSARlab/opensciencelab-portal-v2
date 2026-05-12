import argparse
import csv
from pathlib import Path
from datetime import datetime

import boto3


###############################################################################
#
# Import old OSL access applications from spreadsheet
#
# usage: import_old_user_applications.py [-h] [-f FILE] [-d DEPLOYMENT] [-l LAB] [--dryrun]
#
# options:
#   -h, --help            show this help message and exit
#   -f, --file FILE       CSV file to import
#   -u, --users USERS     list of users granted OSL access
#   -d, --deployment DEPLOYMENT
#                         Deployment prefix (bb, test, prod, etc)
#   -l, --lab LAB         Lab to ingest to (eg smce-test-opensarlab)
#   --dryrun              Don't insert records
#
# NOTE: Requires AWS environment/profile is set up
#############################################################################


class InputError(Exception):
    pass


# Cognito Client
db_client = boto3.client("dynamodb", region_name="us-west-2")
db_resource = boto3.resource("dynamodb", region_name="us-west-2")

# Get cmd line args
parser = argparse.ArgumentParser(description="Import old lab access requests")
parser.add_argument("-f", "--file", type=str, help="CSV file to import")
parser.add_argument("-u", "--users", type=str, help="list of users granted OSL access")
parser.add_argument(
    "-d", "--deployment", type=str, help="Deployment prefix (bb, test, prod, etc)"
)
parser.add_argument(
    "-l", "--lab", type=str, help="Lab to ingest to (eg smce-test-opensarlab)"
)
parser.add_argument("--dryrun", action="store_true", help="Don't insert records")
args = parser.parse_args()

question_map = {
    "sar_experience": "Tell us about your SAR-related experience and the length of time you have worked in the field.\n(10 points)",
    "osl_experience": "Have you used OpenSARLab before? If so, tell us what you used it for and what you produced / developed / delivered with it. (10 points)",
    "use_case": "What do you want to use OpenSARLab for? (20 points)",
    "personal_impacts": "If you were given access to OpenSARLab, what would be the impact for you?\n(20 points)",
    "community_impacts": "What would be the impact for your community? (20 points)",
    "research_impacts": "What would be the impact for the field of research you are contributing to?\n(20 points)",
}


def get_dynamodb_table(deployment, search_string):
    # we should never have > 60
    tables = db_client.list_tables(Limit=100)

    if not deployment:
        raise InputError("No deployment prefix (-d/--deployment) specified")

    for table in tables["TableNames"]:
        if table.startswith(f"PortalCdkStack-{deployment}"):
            if search_string in table:
                return table

    raise InputError(f"{search_string} Table for '{deployment}' not found")


def import_csv(file_path):
    if not Path(file_path).is_file():
        InputError(f"Could not find CSV {file_path}")
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [x for x in reader]


def import_list(user_file):
    all_users = []
    if not Path(user_file).is_file():
        return all_users

    with open(user_file, "r") as file:
        for line in file.read().splitlines():
            line = line.strip()
            if line != "":
                all_users.append(line.lower())

    print(f"Found {len(all_users)} approved users")

    return all_users


def check_if_user_exists(table_name, username):
    if not username:
        return False

    response = db_client.get_item(
        TableName=table_name,
        Key={
            "username": {"S": username},
        },
    )

    if response.get("Item"):
        return True
    return False


def process_csv(data, labname, user_table_name, users):
    insert_rows = {}

    for row in data:
        username = row.get("What is your OpenScienceLab username?").lower()
        if check_if_user_exists(user_table_name, username):
            # User exists, insert into Request table
            request_date = datetime.strptime(row.get("Timestamp"), "%m/%d/%Y %H:%M:%S")
            comments = row.get("Comments")

            if username not in insert_rows:
                request = {
                    "labname": labname,
                    "username": username,
                    "answers": [],
                    "created_at": request_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_update": request_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "approved" if username in users else "imported",
                    "_rec_counter": 1,
                }
            else:
                request = insert_rows[username]
                request["last_update"] = request_date.strftime("%Y-%m-%d %H:%M:%S")

            answers_dict = {
                "submission_date": request_date.strftime("%Y-%m-%d %H:%M:%S"),
                "submission_comment": comments,
                "submission_cc": "??",
                "submission_ip": "??",
                "submission_reviewer": "None",
            }
            for q_name, q_string in question_map.items():
                answers_dict[q_name] = row[q_string]

            # Add answers to the request
            request["answers"].append(answers_dict)

            # Update the request
            insert_rows[username] = request

    return insert_rows


def insert_request(request, request_table):
    response = request_table.put_item(Item=request)
    return response


def import_old_requests(deployment, csv_file, labname, dryrun, user_file):
    request_table_name = get_dynamodb_table(deployment, "RequestsTable")
    user_table_name = get_dynamodb_table(deployment, "lambdadynamodbstack")
    request_data = import_csv(csv_file)
    users = import_list(user_file)
    print("Processing CSV...")
    insert_requests = process_csv(request_data, labname, user_table_name, users)
    request_table = db_resource.Table(request_table_name)
    print("Updating DynamoDB....")
    update_num = 0
    for username, request in insert_requests.items():
        update_num += 1

        print(
            f"Inserting requests for {username} ({update_num}/{len(insert_requests)})"
        )
        if len(request["answers"]) > 1:
            print(" - multiple requests")

        if not (dryrun):
            insert_request(request, request_table)

    return insert_requests


if not args.lab:
    InputError("Must supply a lab name")

if args.dryrun:
    print("%%%%%%%%%\nOnly executing Dryrun!\n%%%%%%%%%")

result = import_old_requests(
    args.deployment, args.file, args.lab, args.dryrun, args.users
)
