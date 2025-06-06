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
