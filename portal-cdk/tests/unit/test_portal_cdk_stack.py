
import pytest

import aws_cdk as core
import aws_cdk.assertions as assertions

from portal_cdk.portal_cdk_stack import PortalCdkStack

# Synthing the stack is expensive, so only do it once at the start of testing:
@pytest.fixture(scope="session")
def portal_template():
    app = core.App()
    stack = PortalCdkStack(app, "portal-cdk")
    template = assertions.Template.from_stack(stack)
    return template

# example tests. To run these tests, uncomment this file along with the example
# resource in portal_cdk/portal_cdk_stack.py
def test_lambda_versions_match(portal_template):
    python_runtime = "python3.11"
    portal_template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": python_runtime,
    })
    portal_template.has_resource_properties("AWS::Lambda::LayerVersion", {
        "CompatibleRuntimes": [python_runtime],
    })
