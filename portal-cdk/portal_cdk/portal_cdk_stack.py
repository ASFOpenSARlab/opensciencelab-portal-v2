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
                memory_size=1024,
            ),
        )

        ### Integration is after the request is validated:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigatewayv2_integrations.HttpLambdaIntegration.html
        lambda_integration = apigwv2_integrations.HttpLambdaIntegration(
            # Added construct_id so we can tell them apart in the console:
            f"LambdaIntegration-{construct_id}",
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
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigatewayv2.AddRoutesOptions.html
        http_api.add_routes(
            path=f"/lab/{LAB_SHORT_NAME}/{{proxy+}}",
            methods=[apigwv2.HttpMethod.ANY],
            integration=lab_integration,
        )

        # Hub endpoint
        http_api.add_routes(
            path="/portal",
            methods=[apigwv2.HttpMethod.ANY],
            integration=lambda_integration,
        )

        ## And a basic CloudFront Endpoint:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront-readme.html#from-an-http-endpoint

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.Distribution.html
        portal_cloudfront = cloudfront.Distribution(
            self,
            "CloudFront-Portal",
            comment=f"To API Gateway ({construct_id})",  # No idea why this isn't just called description....
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.BehaviorOptions.html
            default_behavior=cloudfront.BehaviorOptions(
                # This can't contain a colon, but 'str.replace("https://", "")' doesn't work on tokens....
                # Need to craft the origin manually:
                origin=origins.HttpOrigin(
                    f"{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com"
                ),
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT_AND_SECURITY_HEADERS,
            ),
        )
        
        # Modify these externally from cognito using 
        # https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminUpdateUserAttributes.html
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.ICustomAttribute.html
        custom_attributes={
                "country": cognito.StringAttribute(mutable=True),
                "nasa_email": cognito.StringAttribute(mutable=True),
                "us_gov_email": cognito.StringAttribute(mutable=True),
                "isro_email": cognito.StringAttribute(mutable=True),
                "university_role": cognito.StringAttribute(mutable=True),
            }

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPool.html
        ### NOTE: To change these settings, you HAVE to delete and re-create the stack :(
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"Portal Userpool - {deploy_prefix}",
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.StandardAttributes.html
            standard_attributes=cognito.StandardAttributes(
                # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.StandardAttribute.html
                # All users must have an email:
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True,
                ),
            ),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.ICustomAttribute.html
            custom_attributes=custom_attributes,
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolEmail.html
            email=cognito.UserPoolEmail.with_cognito(reply_to=None),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.Mfa.html
            mfa=cognito.Mfa.OPTIONAL,
            ## The different ways users can get a MFA code:
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.MfaSecondFactor.html
            mfa_second_factor=cognito.MfaSecondFactor(sms=True, otp=True, email=False),
            deletion_protection=bool(deploy_prefix == "prod"),
            # Default removal_policy is always RETAIN:
            removal_policy=(
                RemovalPolicy.RETAIN
                if deploy_prefix == "prod"
                else RemovalPolicy.DESTROY
            ),
            ## Let users create accounts:
            self_sign_up_enabled=True,
            # This is where we can customize info in verification emails/text:
            user_verification=cognito.UserVerificationConfig(),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True,
                phone=False,
            ),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.SignInAliases.html
            sign_in_aliases=cognito.SignInAliases(
                email=False,
                phone=False,
                preferred_username=False,
                username=True,
            ),
            sign_in_case_sensitive=False,
        )

        ## User Pool Client, AKA App Client:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolClient.html
        portal_host_asf = (
            "opensciencelab"
            + ("" if deploy_prefix == "prod" else "-" + deploy_prefix)
            + ".asf.alaska.edu"
        )
        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.OAuthSettings.html
            o_auth=cognito.OAuthSettings(
                # Where to redirect after log IN:
                callback_urls=[
                    f"https://{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com/auth",
                    f"https://{portal_host_asf}/auth",
                    f"https://{portal_cloudfront.distribution_domain_name}/auth",
                ],
                # Where to redirect after log OUT:
                logout_urls=[
                    f"https://{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com/logout",
                    f"https://{portal_host_asf}/logout",
                    f"https://{portal_cloudfront.distribution_domain_name}/logout",
                ],
            ),
            # supported_identity_providers=[
            #     cognito.UserPoolClientIdentityProvider.COGNITO
            # ],
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

        portal_routes = ("access", "profile", "hub")
        for route in portal_routes:
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigatewayv2.AddRoutesOptions.html
            http_api.add_routes(
                path=f"/portal/{route}",
                methods=[apigwv2.HttpMethod.ANY],
                integration=lambda_integration,
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

        lambda_dynamo.lambda_function.add_environment("STACK_REGION", self.region)
        lambda_dynamo.lambda_function.add_environment(
            "CLOUDFRONT_ENDPOINT", f"{portal_cloudfront.distribution_domain_name}"
        )

        # Configuration to allow Cognito OAuth2
        lambda_dynamo.lambda_function.add_environment(
            "COGNITO_CLIENT_ID", user_pool_client.user_pool_client_id
        )
        lambda_dynamo.lambda_function.add_environment(
            "COGNITO_POOL_ID", user_pool.user_pool_id
        )
        lambda_dynamo.lambda_function.add_environment(
            "COGNITO_DOMAIN_ID", user_pool_domain.domain_name
        )

        lambda_dynamo.lambda_function.add_environment(
            "SSO_TOKEN_SECRET_NAME", sso_token_secret.secret_name
        )
        # Grant lambda permssion to read secret manager
        sso_token_secret.grant_read(lambda_dynamo.lambda_function)

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

        CfnOutput(
            self,
            "SSO-TOKEN-ARN",
            value=sso_token_secret.secret_full_arn,
            description="ARN of SSO Token",
        )
