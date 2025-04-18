"""Application to deploy and maintain the OIDC Provider for GitHub Actions"""

#!/usr/bin/env python3
import os

import aws_cdk as cdk

# from user_audit.user_audit_stack import UserAuditStack
from oidc_provider import OidcProviderStack

# User Stack Name
project_name = os.getenv("PROJECT_NAME")
stack_prefix = os.getenv("DEPLOY_PREFIX", "test")
stack_name = project_name if project_name else f"{stack_prefix}-oidc-provider"

app = cdk.App()
OidcProviderStack(
    app,
    stack_name,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)
app.synth()
