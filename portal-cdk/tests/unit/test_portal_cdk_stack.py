"""Unit test for portal_cdk stack."""

import os
import shutil
import pytest

import aws_cdk as core
import aws_cdk.assertions as assertions

from portal_cdk.portal_cdk_stack import PortalCdkStack


@pytest.fixture(scope="session")
def bundle_dir():
    # If layer hasn't been built, make a temporary location
    layer_build_path = "/tmp/.build/lambda/"

    if not os.path.isdir(layer_build_path):
        os.makedirs(os.path.join(layer_build_path, "code"))
        # Yield to come back later and remove
        yield layer_build_path
        shutil.rmtree(str(layer_build_path))
        return layer_build_path

    # If it exists, we don't need anything
    yield layer_build_path
    return layer_build_path


# Synthing the stack is expensive, so only do it once at the start of testing:
@pytest.fixture(scope="session")
def portal_template():
    app = core.App()
    stack = PortalCdkStack(
        app,
        "portal-cdk",
        os.getenv("DEPLOY_PREFIX", "unk"),
    )
    template = assertions.Template.from_stack(stack)
    return template


# example tests. To run these tests, uncomment this file along with the example
# resource in portal_cdk/portal_cdk_stack.py
def test_lambda_versions_match(bundle_dir, portal_template):
    python_runtime = "python3.11"
    portal_template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Runtime": python_runtime,
            "Layers": [
                assertions.Match.any_value(),
                assertions.Match.any_value(),
                ## TODO: Figure out how to get this as one of the two layers above:
                # f"arn:aws:lambda:{self.region}:{self.account}:layer:AWSLambdaPowertoolsPythonV3-{python_runtime.replace('.','')}-x86_64:7",
            ],
        },
    )
    portal_template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {
            "CompatibleRuntimes": [python_runtime],
        },
    )
