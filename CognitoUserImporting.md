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
