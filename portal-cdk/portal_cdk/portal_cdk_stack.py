from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct


class PortalCdkStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, deploy_prefix: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        print(f"INSIDE THE STACK: {deploy_prefix}")
        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "PortalCdkQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
