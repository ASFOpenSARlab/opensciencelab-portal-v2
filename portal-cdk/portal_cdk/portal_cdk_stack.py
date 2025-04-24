from aws_cdk import (
    Stack,
    aws_lambda,
    CfnOutput,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct

from aws_solutions_constructs.aws_lambda_dynamodb import LambdaToDynamoDB

class PortalCdkStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, deploy_prefix: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)


        ##################
        ## Lambda Stuff ##
        ##################
        lambda_runtime = aws_lambda.Runtime.PYTHON_3_12
        ## Get the powertools arn from:
        # https://docs.powertools.aws.dev/lambda/python/latest/
        ## Import it with CDK:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.LayerVersion.html#static-fromwbrlayerwbrversionwbrarnscope-id-layerversionarn
        python_version = lambda_runtime.name.lower().replace('.', '') # pylint: disable=no-member (it's complaining about 'name' for some reason)
        powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            'LambdaPowertoolsLayer',
            f'arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:7', # TODO: Test if this works without the `:7`, so we don't have to keep checking for updates
        )

        # https://constructs.dev/packages/@aws-solutions-constructs/aws-lambda-dynamodb/v/2.84.0?lang=python
        lambda_dynamo = LambdaToDynamoDB(
            self,
            'test_lambda_dynamodb_stack',
            lambda_function_props=aws_lambda.FunctionProps(
                code=aws_lambda.Code.from_asset('lambda'),
                description=f"Powertools API with Dynamo ({construct_id})",
                runtime=aws_lambda.Runtime.PYTHON_3_11,
                handler='main.lambda_handler',
                layers=[powertools_layer],
            ),
        )
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigatewayv2_integrations.HttpLambdaIntegration.html
        lambda_integration = apigwv2_integrations.HttpLambdaIntegration("LambdaIntegration", lambda_dynamo.lambda_function)

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


        ## And a basic CloudFront Endpoint:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront-readme.html#from-an-http-endpoint

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.Distribution.html
        portal_cloudfront = cloudfront.Distribution(
            self,
            "CloudFront-PaymentPortal",
            comment=f"To API Gateway ({construct_id})", # No idea why this isn't just called description....
            default_behavior=cloudfront.BehaviorOptions(
                # This can't contain a colon, but 'str.replace("https://", "")' doesn't work on tokens....
                # Need to craft the origin manually:
                origin=origins.HttpOrigin(f"{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com"),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            )
        )

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.CfnOutput.html
        CfnOutput(self, "URL", value=f"https://{portal_cloudfront.distribution_domain_name}", description="CloudFront URL")
        CfnOutput(self, "URL-HELLO", value=f"https://{portal_cloudfront.distribution_domain_name}/hello", description="Add your name after (url.com/hello/asdf)")
