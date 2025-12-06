import argparse
import requests
import random

## Run in parallel by using the following commands
## Make sure the last command ends in --users-file
# split -l 500 users.txt users
# ls users* | xargs -n1 -P20 python bulk_add_users.py --your-flags --users-file


# usage: bulk_add_users.py [-h] [--portal-jwt PORTAL_JWT] [--portal-username PORTAL_USERNAME]
#                          [--lab-shortname LAB_SHORTNAME] [--domain DOMAIN] [--users-file USERS_FILE] [--profiles PROFILES]
#                          [--delete] [--generate-user-profiles] [-v] [--print-threshold PRINT_THRESHOLD]
#                          [-dcc DESIGNATED_COUNTRY_CHANCE]

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
#   --users-file USERS_FILE
#                         file where list of users to be modified is defined, file is of usernames separated by newlines
#   --profiles PROFILES   profiles to be given to each user, comma separated string
#   --delete              if provided will delete the provided users
#   --generate-user-profiles
#                         if provided will generate random user profiles
#   -v, --verbose         If set will print every successful request. Otherwise print error messages and percentage
#                         completed
#   --print-threshold PRINT_THRESHOLD
#                         Report completion at reported percentage interval Ex: 5 percent is 0.05
#   -dcc DESIGNATED_COUNTRY_CHANCE, --designated-country-chance DESIGNATED_COUNTRY_CHANCE
#                         Percent chance user will have a designated country


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


def generate_profile(designated_country_chance) -> dict:
    profile = {}
    # Add random country, randomly designated countries
    profile["country_of_residence"] = random.choices(
        ["US", "HT"],
        weights=[100 - designated_country_chance, designated_country_chance],
    )
    # Add NASA affiliation
    if random.getrandbits(1):
        profile["is_affiliated_with_nasa"] = "yes"
        if random.getrandbits(1):
            profile["user_or_pi_nasa_email"] = "yes"
            profile["user_affliated_with_nasa_research_email"] = "nasa_user@nasa.gov"
            profile["pi_affliated_with_nasa_research_email"] = ""
        else:
            profile["user_or_pi_nasa_email"] = "no"
            profile["user_affliated_with_nasa_research_email"] = ""
            profile["pi_affliated_with_nasa_research_email"] = "nasa_pi@nasa.gov"
    else:
        profile["is_affiliated_with_nasa"] = "no"
        profile["user_or_pi_nasa_email"] = "no"
        profile["user_affliated_with_nasa_research_email"] = ""
        profile["pi_affliated_with_nasa_research_email"] = ""
    # Add US Gov affiliation
    if random.getrandbits(1):
        profile["is_affiliated_with_us_gov_research"] = "yes"
        profile["user_affliated_with_gov_research_email"] = "gov_user@gov.gov"
    else:
        profile["is_affiliated_with_us_gov_research"] = "no"
        profile["user_affliated_with_gov_research_email"] = ""
    # Add ISRO affiliation
    if random.getrandbits(1):
        profile["is_affliated_with_isro_research"] = "yes"
        profile["user_affliated_with_isro_research_email"] = "isro_user@gov.gov"
    else:
        profile["is_affliated_with_isro_research"] = "no"
        profile["user_affliated_with_isro_research_email"] = ""
    # Add University affiliation
    if random.getrandbits(1):
        profile["is_affliated_with_university"] = "yes"
        # Add user checkboxes
        if random.getrandbits(1):
            profile["faculty_member_affliated_with_university"] = "on"
        if random.getrandbits(1):
            profile["research_member_affliated_with_university"] = "on"
        if random.getrandbits(1):
            profile["graduate_student_affliated_with_university"] = "on"
    else:
        profile["is_affliated_with_university"] = "no"

    return profile


def add_random_profile(url, cookies, username, verbose, designated_country_chance):
    # Set profile
    profile = generate_profile(designated_country_chance)
    res = requests.post(url=url, allow_redirects=False, cookies=cookies, data=profile)

    # Print result
    if res.status_code == 302 and res.text == "\"{'Redirect to /portal'}\"":
        # Print success if verbose
        if verbose:
            print(f"Added profile to {username}")
    else:
        # Print error
        print(
            f"Error adding profile for {username} Code: {res.status_code} Response: {res.text}"
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
        "--users-file",
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

    parser.add_argument(
        "--generate-user-profiles",
        action="store_true",
        help="if provided will generate random user profiles",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="If set will print every successful request. Otherwise print error messages and percentage completed",
    )

    parser.add_argument(
        "--print-threshold",
        type=float,
        help="Report completion at reported percentage interval Ex: 5 percent is 0.05",
        default=0.05,
    )

    parser.add_argument(
        "-dcc",
        "--designated-country-chance",
        type=int,
        help="Percent chance user will have a designated country",
        default=0,
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

    # Add or remove users
    users = read_user_file(args.users_file)
    failed_user_messages = []
    num_completed = 0
    current_logging_threshold = 0
    logging_step = args.print_threshold
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
            allow_redirects=False,
            url=url,
            data=data,
            cookies=cookies,
        )

        # Log output
        if ret.status_code == 302 and ret.headers.get("Location").endswith(
            f"/portal/access/manage/{args.lab_shortname}"
        ):
            # Print Success if verbose
            if args.verbose:
                action_english = "Removed" if args.delete else "Added"
                print(
                    f"{action_english} {username} to {args.lab_shortname} on {args.domain}"
                )
        else:
            # Append error message
            failed_user_messages.append(
                f'Failed to create user "{username}"\nReponse code: {ret.status_code}\nResponse body: {ret.text}'
            )

        # add profile if also adding user
        if action == "add_user" and args.generate_user_profiles:
            profile_url = f"https://{args.domain}/portal/profile/form/{username}"
            add_random_profile(
                profile_url,
                cookies,
                username,
                verbose=args.verbose,
                designated_country_chance=args.designated_country_chance,
            )

        # Update completed count
        num_completed += 1

        # Print percentage if exceeds or matches next step
        completed_percent = num_completed / len(users)
        if completed_percent >= current_logging_threshold:
            print(f"Completed {completed_percent * 100:.2f}%")
            # Update logging threshold, capped at 100%
            current_logging_threshold = min(
                current_logging_threshold + logging_step, 1.0
            )

    # Print failure messages
    if failed_user_messages:
        print(f"Failed to create {len(failed_user_messages)}  users")
        for message in failed_user_messages:
            print(f"{message}\n")


if __name__ == "__main__":
    main()
