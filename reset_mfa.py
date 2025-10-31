import argparse
import json

import boto3


###############################################################################
#
# Reset Cognito User (for resetting MFA)
#
# usage: reset_mfa.py [-h] [-u USER] [-d DEPLOYMENT]
#
# options:
#   -h, --help                      show this help message and exit
#   -u, --user USER                 Username
#   -d, --deployment DEPLOYMENT     Deployment prefix (bb, test, prod, etc)
#
# NOTE: Requires AWS environment/profile is set up
#############################################################################


class InputError(Exception):
    pass


# Cognito Client
cog_client = boto3.client("cognito-idp", region_name="us-west-2")

# Get cmd line args
parser = argparse.ArgumentParser(description="Reset a specific user's MFA")
parser.add_argument("-u", "--user", type=str, help="Username")
parser.add_argument(
    "-d", "--deployment", type=str, help="Deployment prefix (bb, test, prod, etc)"
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


def get_user(username, user_pool_id):
    if not username:
        raise InputError("No username specified")
    return cog_client.admin_get_user(UserPoolId=user_pool_id, Username=username)


def delete_user(username, user_pool_id):
    cog_client.admin_delete_user(UserPoolId=user_pool_id, Username=username)


def recreate_user(user, user_pool_id):
    return cog_client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=user["Username"],
        UserAttributes=[
            attr for attr in user["UserAttributes"] if attr["Name"] != "sub"
        ],
    )


def reset_user(deployment, username):
    try:
        user_pool_id = get_user_pool(args.deployment)
        user = get_user(args.user, user_pool_id)
        delete_user(args.user, user_pool_id)
        return recreate_user(user, user_pool_id)
    except cog_client.exceptions.UserNotFoundException:
        raise InputError(f"User '{args.user}' not found")


result = reset_user(args.deployment, args.user)
print(json.dumps(result, indent=2, default=str))
print(f"User {args.user} reset")
