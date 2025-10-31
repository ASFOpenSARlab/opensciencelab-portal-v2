import argparse
import requests

# Commandline use example
# usage: bulk_add_users.py [-h] [--portal-jwt PORTAL_JWT] [--portal-username PORTAL_USERNAME]
#                          [--lab-shortname LAB_SHORTNAME] [--domain DOMAIN] [--users_file USERS_FILE]
#                          [--profiles PROFILES] [--delete]

# Bulk adds users to a lab with a set of default profiles

# options:
#   -h, --help            show this help message and exit
#   --portal-jwt PORTAL_JWT
#                         active jwt cookie for portal
#   --portal-username PORTAL_USERNAME
#                         active username cookie for portal
#   --lab-shortname LAB_SHORTNAME
#                         shortname of lab which users will be added to
#   --domain DOMAIN       domain of lab deployment
#   --users_file USERS_FILE
#                         file where list of users to be modified is defined, file is of usernames separated by newlines
#   --profiles PROFILES   profiles to be given to each user, comma separated string
#   --delete              if provided will delete the provided users


def read_user_file(path: str) -> list[str]:
    with open(path, "r") as f:
        users = []
        for line in f.readlines():
            # Skip if line is commented
            if line.startswith("#"):
                continue
            # Add user if line is not empty
            if line.strip():
                users.append(line.strip())
        return users


def validate_arguments(args) -> list[str]:
    missing_args = []
    # validate always required args
    if not args.portal_jwt:
        missing_args.append("--portal-jwt")
    if not args.portal_username:
        missing_args.append("--portal-username")
    if not args.domain:
        missing_args.append("--domain")
    if not args.lab_shortname:
        missing_args.append("--lab-shortname")
    if not args.users_file:
        missing_args.append("--users_file")

    # validate required for adding users
    if not args.delete:
        if not args.profiles:
            missing_args.append("--profiles")
    if missing_args:
        raise argparse.ArgumentTypeError(
            f"Required arguments missing: {', '.join(missing_args)}"
        )


def main():
    # Add commandline arguments
    parser = argparse.ArgumentParser(
        description="Bulk adds users to a lab with a set of default profiles"
    )

    parser.add_argument(
        "--portal-jwt",
        type=str,
        help="active jwt cookie for portal",
    )

    parser.add_argument(
        "--portal-username",
        type=str,
        help="active username cookie for portal",
    )

    parser.add_argument(
        "--lab-shortname",
        type=str,
        help="shortname of lab which users will be added to",
    )

    parser.add_argument(
        "--domain",
        type=str,
        help="domain of lab deployment",
    )

    parser.add_argument(
        "--users_file",
        type=str,
        help="file where list of users to be modified is defined, file is of usernames separated by newlines",
    )

    parser.add_argument(
        "--profiles",
        type=str,
        help="profiles to be given to each user, comma separated string",
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="if provided will delete the provided users",
    )

    # Parse and validate args
    args = parser.parse_args()
    validate_arguments(args)

    # Generate endpoint url
    url = f"https://{args.domain}/portal/access/manage/{args.lab_shortname}/edituser"

    # Cookies, move to argparser when complete
    cookies = {
        "portal-jwt": args.portal_jwt,
        "portal-username": args.portal_username,
    }

    # Set action
    action = "remove_user" if args.delete else "add_user"

    # Apply action on users
    users = read_user_file(args.users_file)
    for username in users:
        # Generate user creation data
        data = {
            "username": username,
            "action": action,
            "lab_profiles": args.profiles,
            "time_quota": "",
            "lab_country_status": "something",
        }

        # Add user
        ret = requests.post(
            url=url,
            data=data,
            cookies=cookies,
        )

        if ret.status_code == 200:
            action_english = "Removed" if args.delete else "Added"
            print(
                f"{action_english} {username} to {args.lab_shortname} on {args.domain}"
            )
        else:
            raise Exception(
                f'Failed to create user "{username}"\nResponse body: {ret.text}'
            )


if __name__ == "__main__":
    main()
