from aws_cdk import (
    Stack,
    aws_lambda,
    CfnOutput,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_secretsmanager as secretsmanager,
    SecretValue,
)
from constructs import Construct

from aws_solutions_constructs.aws_lambda_dynamodb import LambdaToDynamoDB

LAMBDA_RUNTIME = aws_lambda.Runtime.PYTHON_3_11


class PortalCdkStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ##################
        ## Lambda Stuff ##
        ##################
        ## Get the powertools arn from:
        # https://docs.powertools.aws.dev/lambda/python/latest/
        ## Import it with CDK:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.LayerVersion.html#static-fromwbrlayerwbrversionwbrarnscope-id-layerversionarn
        python_version = LAMBDA_RUNTIME.name.lower().replace(".", "")  # pylint: disable=no-member
        powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "LambdaPowertoolsLayer",
            f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:7",
        )

        # Provide installs from lambda/requirements.txt
        requirements_layer = aws_lambda.LayerVersion(
            self,
            "RequirementsLayer",
            # /tmp/.build/lambda/ is make in the Makefile @ bundle-deps
            code=aws_lambda.Code.from_asset("/tmp/.build/lambda/"),
            compatible_runtimes=[LAMBDA_RUNTIME],
        )

        # https://constructs.dev/packages/@aws-solutions-constructs/aws-lambda-dynamodb/v/2.84.0?lang=python
        lambda_dynamo = LambdaToDynamoDB(
            self,
            "test_lambda_dynamodb_stack",
            lambda_function_props=aws_lambda.FunctionProps(
                code=aws_lambda.Code.from_asset("lambda"),
                description=f"Powertools API with Dynamo ({construct_id})",
                runtime=LAMBDA_RUNTIME,
                handler="main.lambda_handler",
                layers=[powertools_layer, requirements_layer],
            ),
        )
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigatewayv2_integrations.HttpLambdaIntegration.html
        lambda_integration = apigwv2_integrations.HttpLambdaIntegration(
            "LambdaIntegration",
            lambda_dynamo.lambda_function,
        )

        ###########################
        ## A basic http api for now. A more complex example at:
        # https://github.com/asfadmin/ApigatewayV2/blob/main/apigateway_v2/aws_powertools_lambda_stack.py

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigatewayv2.HttpApi.html
        http_api = apigwv2.HttpApi(
            self,
            "HttpApiPowertools",
            description=f"Http API ({construct_id})",
            default_integration=lambda_integration,
        )

        ## lab proxy
        LAB_SHORT_NAME = "smce-test-opensarlab"
        LAB_DOMAIN = "http://smce-test-1433554573.us-west-2.elb.amazonaws.com"  # If https is broken due to mismatch of SSL cert, try http
        lab_integration = apigwv2_integrations.HttpUrlIntegration(
            f"{LAB_SHORT_NAME}_Integration",
            f"{LAB_DOMAIN}/lab/{LAB_SHORT_NAME}/{{proxy}}",
        )
        http_api.add_routes(
            path=f"/lab/{LAB_SHORT_NAME}/{{proxy+}}",
            methods=[apigwv2.HttpMethod.ANY],
            integration=lab_integration,
        )

        ## And a basic CloudFront Endpoint:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront-readme.html#from-an-http-endpoint

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.Distribution.html
        portal_cloudfront = cloudfront.Distribution(
            self,
            "CloudFront-Portal",
            comment=f"To API Gateway ({construct_id})",  # No idea why this isn't just called description....
            default_behavior=cloudfront.BehaviorOptions(
                # This can't contain a colon, but 'str.replace("https://", "")' doesn't work on tokens....
                # Need to craft the origin manually:
                origin=origins.HttpOrigin(
                    f"{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com"
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            ),
        )

        ### Secrets Manager
        sso_token_secret = secretsmanager.Secret(
            self,
            "SecretManager-SSO_Token",
            secret_string_value=SecretValue.unsafe_plain_text(
                "Change me or you will always fail"
            ),
            description="SSO Token required to communicate with Labs",
        )

        lambda_dynamo.lambda_function.add_environment(
            "SSO_TOKEN_SECRET_NAME", sso_token_secret.secret_name
        )
        # Grant lambda permssion to read secret manager
        sso_token_secret.secret.grantRead(lambda_dynamo.lambda_function)

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.CfnOutput.html
        CfnOutput(
            self,
            "URL",
            value=f"https://{portal_cloudfront.distribution_domain_name}",
            description="CloudFront URL",
        )
        CfnOutput(
            self,
            "URL-HELLO",
            value=f"https://{portal_cloudfront.distribution_domain_name}/hello",
            description="Add your name after (url.com/hello/asdf)",
        )
        CfnOutput(
            self,
            "SSO-TOKEN-ARN",
            value=sso_token_secret.secret_full_arn,
            description="ARN of SSO Token",
        )
