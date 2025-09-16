#!/usr/bin/env python3

import os

import aws_cdk as cdk

from portal_cdk.portal_cdk_stack import PortalCdkStack

required_vars = {}
for var in ["DEPLOY_PREFIX", "SES_DOMAIN", "SES_REPLY_TO_EMAIL"]:
    if not os.getenv(var):
        raise ValueError(f"You forgot an env-var `make <target> -e {var}=<value>`")
    required_vars[var.lower()] = os.getenv(var)

app = cdk.App()
PortalCdkStack(
    app,
    f"PortalCdkStack-{required_vars['deploy_prefix']}",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
    vars=required_vars,
)

app.synth()
