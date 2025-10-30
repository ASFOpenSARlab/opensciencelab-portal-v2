import argparse
import requests

# Commandline use example
# python bulk_add_users.py --portal-jwt <jwt cookie> --portal-username <username cookie> \
# --lab-shortname smce-test-opensarlab --domain opensciencelab-test.asf.alaska.edu \
# --users user1 user2 user3 --profiles "SAR 1,t3a.medium - Dask User,m6a.large"

# You can specify the defaults for any/all of these parameters as below

## EXAMPLE
# PORTAL_JWT = "<JWT Cookie>"
# PORTAL_USERNAME = "<Username Cookie>"
# LAB_SHORTNAME = "smce-test-opensarlab"
# DOMAIN = "opensciencelab-test.asf.alaska.edu"
# USERS = [f"user{num}" for num in range(1,10)]
# PROFILES = "m6a.large,m6a.xlarge"
PORTAL_JWT: str = None
PORTAL_USERNAME: str = None
LAB_SHORTNAME: str = None
DOMAIN: str = None
USERS: list[str] = None
PROFILES: str = None


def main():
    # Add commandline arguments
    parser = argparse.ArgumentParser(
        description="Bulk adds users to a lab with a set of default profiles"
    )

    parser.add_argument(
        "--portal-jwt",
        type=str,
        help="active jwt cookie for portal",
        default=PORTAL_JWT,
    )

    parser.add_argument(
        "--portal-username",
        type=str,
        help="active username cookie for portal",
        default=PORTAL_USERNAME,
    )

    parser.add_argument(
        "--lab-shortname",
        type=str,
        help="shortname of lab which users will be added to",
        default=LAB_SHORTNAME,
    )

    parser.add_argument(
        "--domain",
        type=str,
        help="domain of lab deployment",
        default=DOMAIN,
    )

    parser.add_argument(
        "--users",
        type=str,
        nargs="+",
        help="list of users to be added",
        default=USERS,
    )

    parser.add_argument(
        "--profiles",
        type=str,
        help="profiles to be given to each user, comma separated string",
        default=PROFILES,
    )

    # Parse and validate args
    args = parser.parse_args()
    missing_vals = []
    for arg, val in vars(args).items():
        if not val:
            missing_vals.append(arg)
    if len(missing_vals) > 0:
        raise ValueError(f"Values not provided: {', '.join(missing_vals)}")

    # Generate endpoint url
    url = f"https://{args.domain}/portal/access/manage/{args.lab_shortname}/edituser"

    # Cookies, move to argparser when complete
    cookies = {
        "portal-jwt": args.portal_jwt,
        "portal-username": args.portal_username,
    }

    for username in args.users:
        # Generate user creation data
        data = {
            "username": username,
            "action": "add_user",
        }
        data.update(
            {
                "lab_profiles": args.profiles,
                "time_quota": "",
                "lab_country_status": "something",
            }
        )

        # Add user
        ret = requests.post(
            url=url,
            data=data,
            cookies=cookies,
        )

        if ret.status_code == 200:
            print(f"Added {username} to {args.lab_shortname} on {args.domain}")
        else:
            print(f'Failed to create user "{username}"')


if __name__ == "__main__":
    main()
