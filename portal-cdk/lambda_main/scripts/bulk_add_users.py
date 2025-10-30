import argparse
import requests

## Adds users to a lab in bulk
## Can be used in the command line or by defining the following variables below
## EXAMPLE
# PORTAL_JWT = "<JWT Cookie>"
# PORTAL_USERNAME = "<Username Cookie>"
# LAB_SHORTNAME = "smce-test-opensarlab"
# DOMAIN = "opensciencelab-test.asf.alaska.edu"
# USERS = [f"user{num}" for num in range(1,10)]
# PROFILES = "m6a.large,m6a.xlarge"
PORTAL_JWT = None
PORTAL_USERNAME = None
LAB_SHORTNAME = "smce-test-opensarlab"
DOMAIN = "d1xhhnfz3jf3f5.cloudfront.net"
USERS = [f"user{num}" for num in range(10,20)]
PROFILES = "m6a.large,m6a.xlarge"


def main():
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
        # default="opensciencelab-test.asf.alaska.edu",
    )

    parser.add_argument(
        "--users",
        type=str,
        nargs='+',
        help="list of users to be added",
    )

    parser.add_argument(
        "--profiles",
        type=str,
        help="profiles to be given to each user, comma separated string",
    )

    args = parser.parse_args()

    domain = DOMAIN if DOMAIN else args.domain
    lab_shortname = LAB_SHORTNAME if LAB_SHORTNAME else args.lab_shortname
    url = f"https://{domain}/portal/access/manage/{lab_shortname}/edituser"

    # Cookies, move to argparser when complete
    cookies = {
        "portal-jwt": PORTAL_JWT if PORTAL_JWT else args.portal_jwt,
        "portal-username": PORTAL_USERNAME if PORTAL_USERNAME else args.portal_username,
    }

    users = USERS if USERS else args.users
    for username in users:
        # Generate user creation data
        data = {
            "username": username,
            "action": "add_user",
        }
        data.update({
            "lab_profiles": PROFILES,
            "time_quota": "",
            "lab_country_status": "something",
        })

        # Add user
        ret = requests.post(
            url=url,
            data=data,
            cookies=cookies,
        )

        if ret.status_code != 200:
            print(f"Failed to create user \"{username}\"")


if __name__ == "__main__":
    main()