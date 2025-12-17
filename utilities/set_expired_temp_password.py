from datetime import datetime
import pytz
import argparse
import boto3

###############################################################################
#
# usage: set_expired_temp_password.py [-h] [-u] [-d DEPLOYMENT] [-b BEFORE]
#
# Set user-updatable password for expired temp passwords
#
# options:
#   -h, --help            show this help message and exit
#   -u, --update          Execute password update
#   -d, --deployment DEPLOYMENT
#                         Deployment prefix (bb, test, prod, etc)
#   -b, --before BEFORE   YYYY-MM-DD date format to filter users
#
###############################################################################


utc = pytz.UTC


class InputError(Exception):
    pass


# Cognito Client
cog_client = boto3.client("cognito-idp", region_name="us-west-2")

# Get cmd line args
parser = argparse.ArgumentParser(
    description="Set user-updatable password for expired temp passwords"
)
parser.add_argument(
    "-u", "--update", action="store_true", help="Execute password update"
)
parser.add_argument(
    "-d", "--deployment", type=str, help="Deployment prefix (bb, test, prod, etc)"
)
parser.add_argument(
    "-b", "--before", type=str, help="YYYY-MM-DD date format to filter users"
)
args = parser.parse_args()


def get_user_pool(deployment):
    # we should never have > 60
    pools = cog_client.list_user_pools(MaxResults=60)

    if not deployment:
        raise InputError("No deployment prefix (-d/--deployment) specified")

    for pool in pools["UserPools"]:
        if pool["Name"] == f"Portal Userpool - {deployment}":
            return pool["Id"]

    raise InputError(f"Userpool for '{deployment}' not found")


def get_all_users(user_pool_id):
    users = []
    response = cog_client.list_users(UserPoolId=user_pool_id, Limit=60)
    users.extend(response["Users"])

    # Paginate through the results
    while "PaginationToken" in response:
        pagination_token = response["PaginationToken"]
        response = cog_client.list_users(
            UserPoolId=user_pool_id, PaginationToken=pagination_token, Limit=60
        )
        users.extend(response["Users"])

    return users


def update_expired(deployment, update_flag, before_date_filter):
    before_date = datetime.strptime(before_date_filter, "%Y-%m-%d").replace(tzinfo=utc)
    user_pool_id = get_user_pool(args.deployment)
    all_users = get_all_users(user_pool_id)
    expired_users = [u for u in all_users if u["UserStatus"] == "FORCE_CHANGE_PASSWORD"]
    last_updated_before = [
        u for u in expired_users if u["UserLastModifiedDate"] < before_date
    ]
    return [u["Username"] for u in last_updated_before]


result = update_expired(args.deployment, args.update, args.before)
# print(json.dumps(result, indent=2, default=str))
print(f"Found {len(result)} expired Cognito users")
