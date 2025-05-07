from aws_cdk import (
    Stack,
    aws_lambda,
    CfnOutput,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct

from aws_solutions_constructs.aws_lambda_dynamodb import LambdaToDynamoDB

LAMBDA_RUNTIME = aws_lambda.Runtime.PYTHON_3_11


class PortalCdkStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        deploy_prefix: str,
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

        ### Integration is after the request is validated:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigatewayv2_integrations.HttpLambdaIntegration.html
        lambda_integration = apigwv2_integrations.HttpLambdaIntegration(
            # Added construct_id so we can tell them apart in the console:
            f"LambdaIntegration-{construct_id}",
            lambda_dynamo.lambda_function,
        )

        # Integration that will have a Cognito UserPool Authorizor for Authentication
        lambda_integration_authen = apigwv2_integrations.HttpLambdaIntegration(
            "LambdaIntegration_authen",
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

        portal_routes = ("access", "profile")
        for route in portal_routes:
            http_api.add_routes(
                path=f"/portal/{route}",
                methods=[apigwv2.HttpMethod.ANY],
                integration=lambda_integration_authen,
            )

        ## And a basic CloudFront Endpoint:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront-readme.html#from-an-http-endpoint

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.Distribution.html
        portal_cloudfront = cloudfront.Distribution(
            self,
            "CloudFront-PaymentPortal",
            comment=f"To API Gateway ({construct_id})",  # No idea why this isn't just called description....
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.BehaviorOptions.html
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


        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPool.html
        ### NOTE: To change these settings, you HAVE to delete and re-create the stack :(
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.StandardAttributes.html
            standard_attributes=cognito.StandardAttributes(
                # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.StandardAttribute.html
                # All users must have an email:
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True,
                ),
            ),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolEmail.html
            email=cognito.UserPoolEmail.with_cognito(reply_to=None),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.Mfa.html
            mfa=cognito.Mfa.OPTIONAL,
            ## The different ways users can get a MFA code:
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.MfaSecondFactor.html
            mfa_second_factor=cognito.MfaSecondFactor(sms=True, otp=True, email=False),
            deletion_protection=bool(deploy_prefix == "prod"),
            # Default removal_policy is always RETAIN:
            removal_policy=RemovalPolicy.RETAIN if deploy_prefix == "prod" else RemovalPolicy.DESTROY,
            ## Let users create accounts:
            self_sign_up_enabled=True,
            # This is where we can customize info in verification emails/text:
            user_verification=cognito.UserVerificationConfig(),
            # auto_verify=cognito.AutoVerifiedAttrs(), <-- TODO: Look in to this if email verification doesn't happen.
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.SignInAliases.html
            sign_in_aliases=cognito.SignInAliases(email=True, phone=False, preferred_username=False, username=False),
            sign_in_case_sensitive=False,
        )

        ## User Pool Client, AKA App Client:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolClient.html
        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.OAuthSettings.html
            o_auth=cognito.OAuthSettings(
                # Where to redirect after log IN:
                callback_urls=[f"https://{portal_cloudfront.distribution_domain_name}/portal"],
                # Where to redirect after log OUT:
                logout_urls=[f"https://{portal_cloudfront.distribution_domain_name}/logout"],
            ),
        )

        ## User Pool Domain:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolDomain.html
        user_pool_domain = cognito.UserPoolDomain(
            self,
            "UserPoolDomain",
            user_pool=user_pool,
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolDomainProps.html
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=construct_id.lower(),
            ),
        )

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.CfnOutput.html
        CfnOutput(
            self,
            "CloudFrontURL",
            value=f"https://{portal_cloudfront.distribution_domain_name}/portal",
            description="CloudFront URL",
        )

        CfnOutput(
            self,
            "ApiGatewayURL",
            value=f"https://{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com/portal",
            description="ApiGateway URL",
        )

        CfnOutput(
            self,
            "CognitoURL",
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.SignInUrlOptions.html
            value=user_pool_domain.sign_in_url(
                client=user_pool_client,
                redirect_uri=f"https://{portal_cloudfront.distribution_domain_name}/portal",
            ),
            description="Endpoint for Cognito User Pool Domain",
        )
