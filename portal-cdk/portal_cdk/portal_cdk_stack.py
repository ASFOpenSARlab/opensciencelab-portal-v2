import os
from constructs import Construct

from aws_cdk import (
    Stack,
    aws_lambda,
    CfnOutput,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_apigatewayv2 as apigwv2,
    aws_dynamodb as dynamodb,
    aws_ses as ses,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_secretsmanager as secretsmanager,
    SecretValue,
)
from aws_solutions_constructs.aws_lambda_dynamodb import LambdaToDynamoDB

LAMBDA_RUNTIME = aws_lambda.Runtime.PYTHON_3_11

# I'd like to see this get spun off into CodeAsConfig collocated with the portal code.
LABS = (
    {
        "LAB_SHORT_NAME": "smce-test-opensarlab",
        "LAB_DOMAIN": "smce-test-1433554573.us-west-2.elb.amazonaws.com",
    },
)

# Prefix key within frontend artifact bucket
# This is also used as the cloudfront prefix path for frontend
# If this is changed also update svelte.config.js#7
# Do not include root slash and any possible trailing slashes.
FRONTEND_PREFIX = "ui"


class PortalCdkStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vars: dict,
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
                code=aws_lambda.Code.from_asset("lambda_main"),
                description=f"Powertools API with Dynamo ({construct_id})",
                runtime=LAMBDA_RUNTIME,
                handler="main.lambda_handler",
                layers=[powertools_layer, requirements_layer],
                memory_size=1024,
                environment={
                    "POWERTOOLS_SERVICE_NAME": "APP",
                    "DEBUG": str(vars["deploy_prefix"] != "prod").lower(),
                    "IS_PROD": str(vars["deploy_prefix"] == "prod").lower(),
                    "SES_EMAIL": str(os.getenv("SES_EMAIL")),
                },
            ),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_dynamodb.TableProps.html
            dynamo_table_props=dynamodb.TableProps(
                partition_key=dynamodb.Attribute(
                    name="username",
                    type=dynamodb.AttributeType.STRING,
                ),
                deletion_protection=bool(vars["deploy_prefix"] == "prod"),
                # Default removal_policy is always RETAIN:
                removal_policy=(
                    RemovalPolicy.RETAIN
                    if vars["deploy_prefix"] == "prod"
                    else RemovalPolicy.DESTROY
                ),
            ),
        )
        # Need to do this after, since doing it inside lambda_dynamo would be a circular dependency:
        lambda_dynamo.lambda_function.add_environment(
            "DYNAMO_TABLE_NAME", lambda_dynamo.dynamo_table.table_name
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

        # Loop over Labs and add proxy behaviors
        for lab in LABS:
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront_origins/HttpOrigin.html
            lab_origin = origins.HttpOrigin(
                lab["LAB_DOMAIN"],
                protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                custom_headers={
                    # This *SHOULD* link to the CF Endpoint, but that creates a circular dependency
                    "return-path": f"{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com"
                },
            )

            # LAB_SHORT_NAME, LAB_DOMAIN
            portal_cloudfront.add_behavior(
                path_pattern=f"/lab/{lab['LAB_SHORT_NAME']}/*",
                origin=lab_origin,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
            )

        ## Svelte frontend out of S3
        frontend_bucket = s3.Bucket(
            self,
            "FrontendSvelteBucket",  # Logical ID within the stack
            bucket_name=f"frontend-svelte-{construct_id.lower()}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            public_read_access=False,
        )

        # Define the CloudFront Function code inline
        # Note that javascript curly brackets need to be escaped due to python's format
        # See https://repost.aws/questions/QUYAUeLI2FSoSTR4TygAMBOQ/specifying-different-error-behaviors-for-different-s3-origins-on-cloudfront#AN7rsXLi4iQzOl2EZth3sSYA
        # Serve all traffic through /ui/index.html so that SvelteKit routing will determine where to go.
        frontend_function_code = """
            function handler(event) {{
                const request = event.request;

                let uri = request.uri;
                
                // Full paths that will be appended with a "/index.html". This is to make the urls much more readable.
                // Thses should match the general file path within SvelteKit (sans any prefix).
                // Any other files will pass-through as expected. 
                const shortEndings = [
                    '/{frontend_prefix}',
                    '/{frontend_prefix}/home',
                    '/{frontend_prefix}/login',
                    '/{frontend_prefix}/users',
                    '/{frontend_prefix}/labs',
                    '/{frontend_prefix}/calculator'
                ]
                
                if( shortEndings.some(shortEnding => uri.endsWith(shortEnding)) ){{
                    request.uri = uri + "/index.html"
                }}

                return request;
            }}
        """.format(frontend_prefix=FRONTEND_PREFIX)

        frontend_function = cloudfront.Function(
            self,
            "FrontendFunction",
            code=cloudfront.FunctionCode.from_inline(frontend_function_code),
            runtime=cloudfront.FunctionRuntime.JS_2_0,
        )

        # Add frontend endpoint
        portal_cloudfront.add_behavior(
            path_pattern=f"/{FRONTEND_PREFIX}*",
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront_origins/README.html
            origin=origins.S3BucketOrigin.with_origin_access_control(
                frontend_bucket,
                origin_access_levels=[
                    cloudfront.AccessLevel.READ,
                    cloudfront.AccessLevel.READ_VERSIONED,
                    cloudfront.AccessLevel.LIST,
                    # cloudfront.AccessLevel.WRITE,
                    # cloudfront.AccessLevel.DELETE,
                ],
                custom_headers={"Hello": "World"},
            ),
            function_associations=[
                cloudfront.FunctionAssociation(
                    function=frontend_function,
                    event_type=cloudfront.FunctionEventType.VIEWER_REQUEST,
                )
            ],
            compress=True,
            # origin_request_policy=cloudfront.OriginRequestPolicy.CORS,
            # allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            # cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            # viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
        )

        # Deploy content from a local directory to the S3 bucket
        # Check to see if /code/portal-cdk/svelte/build exists.
        # If it does not, then there is no artifacts to push to the s3 bucket.
        # In that case, don't deploy content
        if os.path.exists("svelte/build"):
            s3deploy.BucketDeployment(
                self,
                "DeployFrontendContentInvalidateCache",
                sources=[s3deploy.Source.asset("svelte/build")],
                destination_bucket=frontend_bucket,
                destination_key_prefix=f"{FRONTEND_PREFIX}/",
                # Optional: Invalidate CloudFront cache if using CloudFront distribution
                distribution=portal_cloudfront,
                distribution_paths=[f"/{FRONTEND_PREFIX}*"],
            )

        ## Hub endpoint
        http_api.add_routes(
            path="/portal",
            methods=[apigwv2.HttpMethod.ANY],
            integration=lambda_integration,
        )

        ## Our Email Identity in SES:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ses.EmailIdentity.html
        ses_identity = ses.EmailIdentity.from_email_identity_name(
            self,
            "ImportedSESEmailIdentity",
            vars["ses_domain"],
        )
        ses_identity.grant_send_email(lambda_dynamo.lambda_function)
        ## Optional Key for Developing, to accept SES emails:
        #    (Since non-prod is a sandbox, you won't receive the email otherwise)
        if os.getenv("DEV_SES_EMAIL"):
            ses.EmailIdentity(
                self,
                "DevSESEmailIdentity",
                identity=ses.Identity.email(os.getenv("DEV_SES_EMAIL")),
            )
        ## Cognito Lambda Endpoint for Signup:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.Function.html
        lambda_cognito_signup = aws_lambda.Function(
            self,
            "LambdaCognitoSignup",
            code=aws_lambda.Code.from_asset("lambda_signup"),
            description=f"Lambda for Cognito Signup ({construct_id})",
            runtime=LAMBDA_RUNTIME,
            handler="main.lambda_handler",
        )

        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPool.html
        ### NOTE: To change these settings, you HAVE to delete and re-create the stack :(
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"Portal Userpool - {vars['deploy_prefix']}",
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
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolSESOptions.html
            email=cognito.UserPoolEmail.with_ses(
                from_email=f"osl@{ses_identity.email_identity_name}",
                reply_to=vars["ses_email"],
                from_name="ASF OpenScienceLab",
                ses_verified_domain=ses_identity.email_identity_name,
            ),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.Mfa.html
            mfa=cognito.Mfa.REQUIRED,
            ## The different ways users can get a MFA code:
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.MfaSecondFactor.html
            mfa_second_factor=cognito.MfaSecondFactor(sms=True, otp=True, email=False),
            deletion_protection=bool(vars["deploy_prefix"] == "prod"),
            # Default removal_policy is always RETAIN:
            removal_policy=(
                RemovalPolicy.RETAIN
                if vars["deploy_prefix"] == "prod"
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
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolTriggers.html#presignup
            lambda_triggers=cognito.UserPoolTriggers(
                pre_sign_up=lambda_cognito_signup,
            ),
        )

        ## User Pool Client, AKA App Client:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito.UserPoolClient.html
        portal_host_asf = (
            "opensciencelab"
            + ("" if vars["deploy_prefix"] == "prod" else "-" + vars["deploy_prefix"])
            + ".asf.alaska.edu"
        )
        user_pool_client = user_pool.add_client(
            "UserPoolClient",
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
        user_pool_domain = user_pool.add_domain(
            "UserPoolDomain",
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
            # The console removes non-alpha stuff, so this'll be 'SSOTokenCs<RANDOM-HASH>' or something:
            f"SSO-Token-{vars['deploy_prefix'].title()}",
            secret_string_value=SecretValue.unsafe_plain_text(
                "Change me or you will always fail"
            ),
            description=f"({construct_id}) SSO Token required to communicate with Labs",
        )

        lambda_dynamo.lambda_function.add_environment("STACK_REGION", self.region)
        lambda_dynamo.lambda_function.add_environment(
            "CLOUDFRONT_ENDPOINT", f"{portal_cloudfront.distribution_domain_name}"
        )

        # Allow lambda to delete users from cognito
        lambda_dynamo.lambda_function.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cognito-idp:DescribeUserPool",
                    "cognito-idp:ListUsers",
                    "cognito-idp:AdminInitiateAuth",
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminDeleteUser",
                    "cognito-idp:AdminGetUser",
                ],
                resources=[user_pool.user_pool_arn],
            )
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

        CfnOutput(
            self,
            "return-path-whitelist-value",
            value=f"{http_api.http_api_id}.execute-api.{self.region}.amazonaws.com",
            description="The return-path value that needs to be added to Lab whitelists (for non-prod)",
        )
