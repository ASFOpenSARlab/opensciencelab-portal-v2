#!/usr/bin/env python3

import os

import aws_cdk as cdk

from portal_cdk.portal_cdk_stack import PortalCdkStack

# NOT using 'get' here, so that we fail fast if this isn't set.
# (you should be using the makefile to deploy this...)
maturity = os.environ['MATURITY']

app = cdk.App()
PortalCdkStack(
    app,
    f"PortalCdkStack-{maturity}",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION'),
    ),
    maturity=maturity,
)

app.synth()
