from aws_cdk import (
    Stack, Tags,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elb_v2,
)
from constructs import Construct

class AwsStackStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC information
        vpc = ec2.Vpc.from_lookup(
            self, 'VPC',
            vpc_name='sample-vpc',
            is_default=False)

        # ECS cluster, generic
        cluster = ecs.Cluster(self, 'MyCluster', vpc=vpc)

        # ECS task with the OpenAI API key as a secret
        task_image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            # イメージの指定方法はもう少し確認しよう
            # https://github.com/aws/aws-cdk/discussions/29846
            image=ecs.ContainerImage.from_asset('./server'),
            container_port=8000, #ここは同じでOK
            secrets={
                'OPENAI_API_KEY': ecs.Secret.from_ssm_parameter(
                    ssm.StringParameter.from_secure_string_parameter_attributes(
                        self, "OpenAIParam",
                        parameter_name="OPENAI_API_KEY",
                        version=1
                    )
                ),
                'TAVILY_API_KEY': ecs.Secret.from_ssm_parameter(
                    ssm.StringParameter.from_secure_string_parameter_attributes(
                        self, "TavliyApiKey",
                        parameter_name="TAVILY_API_KEY",
                        version=1
                    )
                ),
                'GOOGLE_API_KEY': ecs.Secret.from_ssm_parameter(
                    ssm.StringParameter.from_secure_string_parameter_attributes(
                        self, "GoogleApiKey",
                        parameter_name="GOOGLE_API_KEY",
                        version=1
                    )
                ),
                'CUSTOM_SEARCH_ENGINE_ID': ecs.Secret.from_ssm_parameter(
                    ssm.StringParameter.from_secure_string_parameter_attributes(
                        self, "CustomSearchEngine",
                        parameter_name="CUSTOM_SEARCH_ENGINE_ID",
                        version=1
                    )
                ),
                'GMAIL_ADDRESS': ecs.Secret.from_ssm_parameter(
                    ssm.StringParameter.from_secure_string_parameter_attributes(
                        self, "GmailAddress",
                        parameter_name="GMAIL_ADDRESS",
                        version=1
                    )
                ),
                'GMAIL_APP_PASSWORD': ecs.Secret.from_ssm_parameter(
                    ssm.StringParameter.from_secure_string_parameter_attributes(
                        self, "GmailAppPassword",
                        parameter_name="GMAIL_APP_PASSWORD",
                        version=1
                    )
                ),
                'ANTHROPIC_API_KEY': ecs.Secret.from_ssm_parameter(
                    ssm.StringParameter.from_secure_string_parameter_attributes(
                        self, "AnthropicApiKey",
                        parameter_name="ANTHROPIC_API_KEY",
                        version=1
                    )
                ),
            }
        )

        # Use ALB + Fargate from ECS patterns, through HTTPS
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, 'FastApiWithFargate',
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            assign_public_ip=True,
            task_image_options=task_image_options,
            public_load_balancer=True,
            # Since no specific domain is used, HTTPS configuration is removed
            protocol=elb_v2.ApplicationProtocol.HTTP
        )

        # Default health check
        service.target_group.configure_health_check(path='/health')