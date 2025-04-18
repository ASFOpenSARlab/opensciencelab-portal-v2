""" Stack for OIDC Provider """
from pathlib import Path
import configparser

from constructs import Construct

from aws_cdk import Stack
from aws_cdk import aws_iam as iam

GITHUB_RUNNER_THUMBPRINTS = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

class OidcProviderStack(Stack):
    """ Basic Stack """
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get github repos allowed to talk with AWS
        github_repos_file = Path(__file__).resolve().parent / "github_repos.conf"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(github_repos_file)
        git_repo_list = list(config['GitHubRepos'])

        # Generic CDK enabling policy to attach to all the roles.
        generic_cdk_policy = iam.Policy(self, "generic-cdk-policy",
            statements=self._get_cdk_iam_policy(),
            policy_name=f"generic-cdk-policy-{self.region}",
            force=True,
        )

        # I hate having this here, but need to find a better way to pass self.account/self.account
        cdk_deploy_roles = {
            "deploy_oidc_provider_stack_role": {
                "description": "IAM Role for OIDC Provider Access",
                "name": "AllowUpdateOIDCStack",
                "statements": [
                    {
                        "effect": "allow",
                        "actions": ["cloudformation:*"],
                        "resources": [
                            f"arn:aws:cloudformation:{self.region}:{self.account}:stack/*-oidc-provider/*",
                        ]
                    },
                    {
                        "effect": "allow",
                        "actions": ["iam:*"],
                        "resources": [
                            f"arn:aws:iam::{self.account}:role/oidc_provider_stack_role"
                        ]
                    }
                ]
            },
        }

        # GitHub OIDC Provier
        github_provider = iam.OpenIdConnectProvider(self, "GitHubOIDC",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
            thumbprints=GITHUB_RUNNER_THUMBPRINTS
        )

        # Resusable Federated Principal
        repos_with_access_stmt = [ f"repo:{repos}:*" for repos in git_repo_list ]

        federated_principal = iam.FederatedPrincipal(
            federated=github_provider.open_id_connect_provider_arn,
            assume_role_action="sts:AssumeRoleWithWebIdentity",
            conditions={
                "ForAnyValue:StringLike": {
                    "token.actions.githubusercontent.com:sub": repos_with_access_stmt,
                },
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                },
            },
        )

        for role_name, params in cdk_deploy_roles.items():
            # Create a role for each project
            created_role = iam.Role(self, role_name,
                role_name=role_name,
                assumed_by=federated_principal,
                description=params["description"],
                inline_policies=self._create_policy_doc( params["name"], params["statements"] )
            )
            # Attach generic_cdk_policy to this role
            generic_cdk_policy.attach_to_role(created_role)

    # Convert policy dict into policy statement object
    @staticmethod
    def _format_policy( statement ) -> iam.PolicyStatement:
        effect=iam.Effect.ALLOW if statement["effect"].upper() == "ALLOW" else iam.Effect.DENY
        return iam.PolicyStatement(
            effect=effect,
            actions=statement.get("actions"),
            resources=statement.get("resources"),
            conditions=statement.get("conditions")
        )

    def _get_cdk_iam_policy(self) -> list:
        return [
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudformation:*"],
                resources=[f"arn:aws:cloudformation:{self.region}:{self.account}:stack/CDKToolkit/*"]
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:*"],
                resources=[f"arn:aws:s3:::cdk-*-assets-{self.account}-{self.region}"]
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:ListAllMyBuckets"],
                resources=["*"]
            ),
            # Generic privs for reading input for setting ENV Vars.
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudformation:DescribeStacks",
                    "rds:DescribeDBClusters",
                    "secretsmanager:ListSecrets",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeSubnets"
                ],
                resources=["*"]
            ),
            # Permissions to read account context information
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "acm:ListCertificates",
                    "ec2:DescribeVpcs"
                ],
                resources=["*"]
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/cdk-bootstrap/*"]
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["iam:PassRole", "sts:AssumeRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-*"]
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:*"],
                resources=[f"arn:aws:lambda:{self.region}:{self.account}:function:*CustomAWSCDK*"]
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
                conditions={
                    "ForAnyValue:StringEquals": {
                        "aws:CalledVia": [
                            "cloudformation.amazonaws.com"
                        ]
                    }
                }
            )
        ]

    # Convert a list of statements into a fully policy doc object
    def _create_policy_doc(self, name, statements) -> dict:
        all_policies = []

        for policy in statements:
            all_policies.append( self._format_policy( policy ) )

        return {
            name: iam.PolicyDocument( statements=all_policies )
        }
