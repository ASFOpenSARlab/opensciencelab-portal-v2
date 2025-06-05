"""
This file sets up ENV VARs for tests

https://stackoverflow.com/a/50610630/21674565
"""

import os


os.environ["STACK_REGION"] = "us-west-2"
os.environ["COGNITO_CLIENT_ID"] = "fake-cognito-id"
os.environ["COGNITO_POOL_ID"] = "fake-pool-id"
