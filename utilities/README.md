# User Migration

```
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

```
Created user dgpalmieri in DynamoDB
EXCEPTION THROWN 
 An error occurred (UsernameExistsException) when calling the AdminCreateUser operation: User account already exists 
 for username dgpalmieri
Created user bbuechle in DynamoDB
Created user bbuechle in Cognito
```

A successful execution looks like:

```
$ make cognito 
AWS_ACCESS_KEY_ID="<ID>" AWS_SECRET_ACCESS_KEY="<KEY>" python3 dump_users.py -t "<TABLE_ID>" -p "<POOL_ID>" -w 13 --cognito
Created user dgpalmieri in DynamoDB
Created user dgpalmieri in Cognito
$
```

