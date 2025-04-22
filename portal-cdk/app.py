#!/usr/bin/env python3

import os

import aws_cdk as cdk

from portal_cdk.portal_cdk_stack import PortalCdkStack

deploy_prefix = os.getenv("DEPLOY_PREFIX")

default_maturity = deploy_prefix if deploy_prefix in ["prod", "test"] else "dev"
maturity = os.getenv("MATURITY", default_maturity)

# Default to DEPLOY_PREFIX first, then MATURITY:
stack_id = deploy_prefix or maturity

app = cdk.App()
PortalCdkStack(
    app,
    f"PortalCdkStack-{stack_id}",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
    stack_id=stack_id,
)

app.synth()
