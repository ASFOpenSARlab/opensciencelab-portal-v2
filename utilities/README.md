# Utility Scripts Documentation

Table of Contents

* [User Migration](#user-migration)
* [Bulk Add Users](#bulk-add-users)

## User Migration

```sh
$ python3 dump_users.py -h
usage: dump_users.py [-h] [-c] -t DYNAMO_TABLE -p USER_POOL_ID -w ACTIVE_WINDOW_START [-u USER_DATABASE_PATH]
                     [-a AUTH_DATABASE_PATH]

Migrate users from OSL Portal v1 to v2

optional arguments:
  -h, --help            show this help message and exit
  -c, --cognito         Create cognito accounts for all users
  -t DYNAMO_TABLE, --dynamo-table-name DYNAMO_TABLE
                        The DynamoDB table name for the migration destination
  -p USER_POOL_ID, --user-pool-id USER_POOL_ID
                        The Cognito User Pool ID for the migration destination
  -w ACTIVE_WINDOW_START, --active-window-start ACTIVE_WINDOW_START
                        The number of months in the past to start the 'active user' migration window
  -u USER_DATABASE_PATH, --user-database-path USER_DATABASE_PATH
                        The POSIX file path of the user access database
  -a AUTH_DATABASE_PATH, --auth-database-path AUTH_DATABASE_PATH
                        The POSIX file path of the nativeauthenticator database
```

for ease of use/editing, I added a temporary Makefile with this structure:

```Makefile
default:
        AWS_ACCESS_KEY_ID="" AWS_SECRET_ACCESS_KEY="" python3 dump_users.py -t "" -p "" -w 13

cognito:
        AWS_ACCESS_KEY_ID="" AWS_SECRET_ACCESS_KEY="" python3 dump_users.py -t "" -p "" -w 13 --cognito
```

this enables you to not load your AWS credentials into the environment and not
to have to set long strings on the command line every time.

With the above pattern, the ideal usage is `make [cognito] | tee out.txt`, as
the script catches and prints errors, rather than throwing and exiting in a
failed state. For example:

```sh
Created user dgpalmieri in DynamoDB
EXCEPTION THROWN 
 An error occurred (UsernameExistsException) when calling the AdminCreateUser operation: User account already exists 
 for username dgpalmieri
Created user bbuechle in DynamoDB
Created user bbuechle in Cognito
```

A successful execution looks like:

```sh
$ make cognito 
AWS_ACCESS_KEY_ID="<ID>" AWS_SECRET_ACCESS_KEY="<KEY>" python3 dump_users.py -t "<TABLE_ID>" -p "<POOL_ID>" -w 13 --cognito
Created user dgpalmieri in DynamoDB
Created user dgpalmieri in Cognito
$
```

## Bulk Add Users

```sh
usage: bulk_add_users.py [-h] [--portal-jwt PORTAL_JWT] [--portal-username PORTAL_USERNAME]
                         [--lab-shortname LAB_SHORTNAME] [--domain DOMAIN] [--users-file USERS_FILE]
                         [--profiles PROFILES] [--remove-users] [--generate-user-profiles] [-v]
                         [--print-threshold PRINT_THRESHOLD] [-dcc DESIGNATED_COUNTRY_CHANCE]

Bulk adds users to a lab with a set of default profiles

options:
  -h, --help            show this help message and exit
  --portal-jwt PORTAL_JWT
                        active jwt cookie for portal
  --portal-username PORTAL_USERNAME
                        active username cookie for portal
  --lab-shortname LAB_SHORTNAME
                        shortname of lab which users will be added to
  --domain DOMAIN       domain of portal deployment
  --users-file USERS_FILE
                        file where list of users to be modified is defined, file is of usernames separated by newlines
  --profiles PROFILES   profiles to be given to each user, comma separated string
  --remove-users        if provided will remove the provided users from the given lab
  --generate-user-profiles
                        if provided will generate random user profiles
  -v, --verbose         If set will print every successful request. Otherwise print error messages and percentage
                        completed
  --print-threshold PRINT_THRESHOLD
                        Report completion at reported percentage interval Ex: 5 percent is 0.05
  -dcc DESIGNATED_COUNTRY_CHANCE, --designated-country-chance DESIGNATED_COUNTRY_CHANCE
                        Percent chance user will have a designated country
```

### Requirements

* An Admin user's `portal-jwt` and `portal-username` jwt cookies
* A file of usernames delimited by newlines

### Modes

* Add users to lab (Default Behavior) (Creates new user)
  * Add the following flags
    * --portal-jwt
    * --portal-username
    * --lab-shortname
    * --domain
    * --users-file
  * Give provided users a random profile by adding this flag (useful for generating new users)
    * --generate-user-profiles
* Remove selected users from lab (Does not delete user)
  * Add the following flags
    * --portal-jwt
    * --portal-username
    * --lab-shortname
    * --domain
    * --users-file
    * --remove-users

### Running in Parallel

You can run this script in parallel by following these steps

1. Split your user file into equal parts with the command \
   `split -l 200 users.txt users` \
   This will split your `users.txt` file into a number of files of 200 lines each with a name matching the pattern `users*`
2. Run the script using xargs parallelization \
   `ls users* | xargs -n1 -P20 python bulk_add_users.py --your-flags --users-file` \
   Replace `--your-flags` with all flags you are providing except for `--users-file` which must be at the end of the command
