# Lambda Unit Testing

## Directory Structure

`pytest` automatically crawls everything here, and adds any file named `test_*.py` to it's suite.

To make tests easy to find and organized, this test suite has the same exact structure as the `portal-cdk/lambda` directory. This means that if you want to find the tests for a specific file, you can just look in the same relative path in this directory.

- For example, the tests for `../lambda/utils/user/user.py` are located in `./utils/user/test_user.py`.

## Sharing Code between Test Files (`conftest.py`)

You can use [conftest.py](https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files) files to share code between tests. They are shared with any tests that are in that directory or any subdirectory (NOT before). We have one in the root of lambda, [one directory before](../conftest.py). (I tried moving it to this directory, but it broke paths. I could NOT figure out why). But we can have as many as we want, wherever.

## Faking (or Mocking) AWS Services for Tests

We use [moto](https://docs.getmoto.org/en/latest/) for this. You can use it to easily patch any boto3 client/resource/whatever, and it'll create a virtual version for you to work against. This is useful for testing code that interacts with AWS services, like S3, DynamoDB, etc.

For a complete example, see the [test_user.py](./util/user/test_user.py) file on testing with classes.

## Hitting the API with the `requests` Library

- Log into your portal through `Cognito`, so it creates the cookies you'll need.
- Grab the cookies with `Right-Click` -> `Inspect` -> `Application` (Might be behind three `...`). You'll see `portal-jwt` and `portal-username`. You'll need both

- Export them in your shell:

  ```bash
  export PORTAL_JWT=<your_portal_jwt>
  export PORTAL_USERNAME=<your_portal_username>
  ```

- Use them in a python shell:

  ```python
  import os
  import requests

  # Set the cookies
  cookies = {
      "portal-jwt": os.environ.get("PORTAL_JWT"),
      "portal-username": os.environ.get("PORTAL_USERNAME"),
  }
  url = "https://abc123def456.cloudfront.net"

  # Make a GET request:
  response = requests.get(f"{url}/endpoint", cookies=cookies)

  # Or PUT:
  response = requests.put(f"{url}/endpoint", cookies=cookies, json={"key": "value"})

  # For Example:
  >>> r = requests.put(f"{url}/portal/access/labs/basic_user", cookies=cookies, json={'labs':{'shortname2':{"lab_profiles":["m6a.large"],"can_user_access_lab":True, "can_user_see_lab_card":True, "time_quota":"","lab_country_status":"protected"}}})
  >>> r.content
  b'{"result": "Success", "body": {"labs": {"shortname2": {"lab_profiles": ["m6a.large"], "can_user_access_lab": true, "can_user_see_lab_card": true, "time_quota": "", "lab_country_status": "protected"}}}}'
  ```

- If you have to test with MALFORMED json, you can't use the `json={'a':1}` or it'll fix the json for you (the error being `'` instead of `"` around the `a`). String is technically valid json, so you can't do `json="asdf"` or `json="{'a':1}"` either.

  - Craft the json yourself like this (use `data` instead of `json`, and add the content-type header). The error here is using `'` instead of `"` to wrap the `a`.

  ```python
  >>> r = requests.delete(f"{url}/portal/access/labs/basic_user", data="{'a':1}", cookies=cookies, headers={"Content-Type": "application/json"})
  ```
