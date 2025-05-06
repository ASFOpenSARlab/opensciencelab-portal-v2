#!/usr/bin/env python3

import os

import aws_cdk as cdk

from portal_cdk.portal_cdk_stack import PortalCdkStack

deploy_prefix = os.getenv("DEPLOY_PREFIX")
if not deploy_prefix:
    raise ValueError("You forgot an env-var `make <target> -e DEPLOY_PREFIX=<you>`")

app = cdk.App()
PortalCdkStack(
    app,
    f"PortalCdkStack-{deploy_prefix}",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
    # deploy_prefix=deploy_prefix,
)

app.synth()
