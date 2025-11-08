"""
CDK Stack for Socratic Benchmarking Platform.

Architecture:
- EventBridge (weekly cron) → Planner Lambda
- Planner → SQS dialogue-jobs → Runner Lambda (parallel)
- Runner → SQS judge-jobs → Judge Lambda (parallel)
- Judge → EventBridge run.judged → Curator Lambda
- Curator → DynamoDB + S3
- API Gateway + Read Lambda → Static UI
"""
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_events,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct


class SocraticBenchStack(Stack):
    """Main infrastructure stack."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========================================
        # Data Layer
        # ========================================

        # S3 Buckets
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"socratic-bench-data-{self.account}",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                # Archive raw data to Glacier after 90 days
                s3.LifecycleRule(
                    id="ArchiveRawData",
                    prefix="raw/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90),
                        )
                    ],
                ),
            ],
            removal_policy=RemovalPolicy.RETAIN,
        )

        # DynamoDB Table (single table design)
        self.table = dynamodb.Table(
            self,
            "SocraticTable",
            table_name="socratic_core",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # GSI1: Query by model
        self.table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI2: Query by manifest
        self.table.add_global_secondary_index(
            index_name="GSI2",
            partition_key=dynamodb.Attribute(
                name="GSI2PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI2SK", type=dynamodb.AttributeType.STRING
            ),
        )

        # ========================================
        # Message Queues
        # ========================================

        # Dialogue jobs queue (Planner → Runner)
        dialogue_dlq = sqs.Queue(
            self,
            "DialogueDLQ",
            queue_name="socratic-dialogue-dlq",
            retention_period=Duration.days(14),
        )

        self.dialogue_queue = sqs.Queue(
            self,
            "DialogueQueue",
            queue_name="socratic-dialogue-jobs",
            visibility_timeout=Duration.minutes(15),  # Max Lambda runtime
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3, queue=dialogue_dlq
            ),
        )

        # Judge jobs queue (Runner → Judge)
        judge_dlq = sqs.Queue(
            self,
            "JudgeDLQ",
            queue_name="socratic-judge-dlq",
            retention_period=Duration.days(14),
        )

        self.judge_queue = sqs.Queue(
            self,
            "JudgeQueue",
            queue_name="socratic-judge-jobs",
            visibility_timeout=Duration.minutes(5),
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=judge_dlq),
        )

        # ========================================
        # EventBridge
        # ========================================

        # Custom event bus for run.judged events
        self.event_bus = events.EventBus(
            self, "SocraticEventBus", event_bus_name="socratic-bench"
        )

        # ========================================
        # Lambda Layers (shared library)
        # ========================================

        self.socratic_lib_layer = lambda_.LayerVersion(
            self,
            "SocraticLibLayer",
            code=lambda_.Code.from_asset("../lib"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="Socratic Bench shared library with dependencies",
        )

        # ========================================
        # Lambda Functions
        # ========================================

        # Common environment variables
        common_env = {
            "TABLE_NAME": self.table.table_name,
            "BUCKET_NAME": self.data_bucket.bucket_name,
            "DIALOGUE_QUEUE_URL": self.dialogue_queue.queue_url,
            "JUDGE_QUEUE_URL": self.judge_queue.queue_url,
            "EVENT_BUS_NAME": self.event_bus.event_bus_name,
        }

        # Planner Lambda
        self.planner_fn = lambda_.Function(
            self,
            "PlannerFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../lambdas/planner"),
            handler="handler.lambda_handler",
            timeout=Duration.minutes(5),
            memory_size=512,
            environment=common_env,
            layers=[self.socratic_lib_layer],
        )

        # Runner Lambda
        self.runner_fn = lambda_.Function(
            self,
            "RunnerFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../lambdas/runner"),
            handler="handler.lambda_handler",
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment=common_env,
            layers=[self.socratic_lib_layer],
            reserved_concurrent_executions=25,  # Limit concurrency
        )

        # Judge Lambda
        self.judge_fn = lambda_.Function(
            self,
            "JudgeFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../lambdas/judge"),
            handler="handler.lambda_handler",
            timeout=Duration.minutes(5),
            memory_size=512,
            environment=common_env,
            layers=[self.socratic_lib_layer],
            reserved_concurrent_executions=25,
        )

        # Curator Lambda
        self.curator_fn = lambda_.Function(
            self,
            "CuratorFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../lambdas/curator"),
            handler="handler.lambda_handler",
            timeout=Duration.minutes(5),
            memory_size=512,
            environment=common_env,
            layers=[self.socratic_lib_layer],
        )

        # Read API Lambda
        self.api_fn = lambda_.Function(
            self,
            "ApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("../lambdas/api"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment=common_env,
            layers=[self.socratic_lib_layer],
        )

        # ========================================
        # IAM Permissions
        # ========================================

        # Planner: read DynamoDB config, write manifest, send SQS
        self.table.grant_read_write_data(self.planner_fn)
        self.data_bucket.grant_read_write(self.planner_fn, "manifests/*")
        self.data_bucket.grant_read(self.planner_fn, "artifacts/*")
        self.dialogue_queue.grant_send_messages(self.planner_fn)

        # Runner: read/write DynamoDB runs/turns, write raw S3, send judge jobs
        self.table.grant_read_write_data(self.runner_fn)
        self.data_bucket.grant_read_write(self.runner_fn, "raw/*")
        self.data_bucket.grant_read(self.runner_fn, "artifacts/*")
        self.judge_queue.grant_send_messages(self.runner_fn)

        # Judge: read raw S3, write judge JSON, update DynamoDB, send events
        self.table.grant_read_write_data(self.judge_fn)
        self.data_bucket.grant_read_write(self.judge_fn, "raw/*")
        self.event_bus.grant_put_events_to(self.judge_fn)

        # Curator: read DynamoDB, write curated S3
        self.table.grant_read_write_data(self.curator_fn)
        self.data_bucket.grant_read(self.curator_fn, "raw/*")
        self.data_bucket.grant_write(self.curator_fn, "curated/*")

        # API: read DynamoDB, read curated AND raw S3 (needs raw for judge dimension scores)
        self.table.grant_read_data(self.api_fn)
        self.data_bucket.grant_read(self.api_fn, "curated/*")
        self.data_bucket.grant_read(self.api_fn, "raw/*")

        # Grant Bedrock access to all functions that need it
        bedrock_policy = iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"],  # Or specify specific model ARNs
        )
        self.runner_fn.add_to_role_policy(bedrock_policy)
        self.judge_fn.add_to_role_policy(bedrock_policy)

        # ========================================
        # Event Triggers
        # ========================================

        # Weekly cron: Monday 3 AM UTC
        weekly_rule = events.Rule(
            self,
            "WeeklyTrigger",
            schedule=events.Schedule.cron(minute="0", hour="3", week_day="MON"),
            description="Trigger weekly Socratic benchmark run",
        )
        weekly_rule.add_target(targets.LambdaFunction(self.planner_fn))

        # SQS trigger for Runner
        self.runner_fn.add_event_source(
            lambda_events.SqsEventSource(
                self.dialogue_queue, batch_size=1, max_concurrency=25
            )
        )

        # SQS trigger for Judge
        self.judge_fn.add_event_source(
            lambda_events.SqsEventSource(
                self.judge_queue, batch_size=1, max_concurrency=25
            )
        )

        # EventBridge trigger for Curator (run.judged)
        run_judged_rule = events.Rule(
            self,
            "RunJudgedRule",
            event_bus=self.event_bus,
            event_pattern=events.EventPattern(detail_type=["run.judged"]),
        )
        run_judged_rule.add_target(targets.LambdaFunction(self.curator_fn))

        # ========================================
        # API Gateway
        # ========================================

        api = apigw.RestApi(
            self,
            "SocraticApi",
            rest_api_name="Socratic Bench API",
            description="Read API for Socratic benchmark results",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
        )

        # API key for auth (simple MVP auth)
        api_key = api.add_api_key("ApiKey")
        usage_plan = api.add_usage_plan(
            "UsagePlan",
            throttle=apigw.ThrottleSettings(rate_limit=100, burst_limit=200),
        )
        usage_plan.add_api_key(api_key)

        # Lambda integration
        integration = apigw.LambdaIntegration(self.api_fn)

        # Routes
        weekly = api.root.add_resource("weekly")
        weekly.add_method("GET", integration, api_key_required=True)

        runs = api.root.add_resource("runs")
        run_id = runs.add_resource("{run_id}")
        summary = run_id.add_resource("summary")
        summary.add_method("GET", integration, api_key_required=True)

        turns = run_id.add_resource("turns")
        turns.add_method("GET", integration, api_key_required=True)

        # New API routes (no API key required for public dashboard)
        api_resource = api.root.add_resource("api")
        timeseries = api_resource.add_resource("timeseries")
        timeseries.add_method("GET", integration, api_key_required=False)

        rankings = api_resource.add_resource("latest-rankings")
        rankings.add_method("GET", integration, api_key_required=False)

        cost_analysis = api_resource.add_resource("cost-analysis")
        cost_analysis.add_method("GET", integration, api_key_required=False)

        detailed_results = api_resource.add_resource("detailed-results")
        detailed_results.add_method("GET", integration, api_key_required=False)

        model_comparison = api_resource.add_resource("model-comparison")
        model_comparison.add_method("GET", integration, api_key_required=False)

        usage_plan.add_api_stage(stage=api.deployment_stage)

        # ========================================
        # Static UI (S3 + CloudFront)
        # ========================================

        ui_bucket = s3.Bucket(
            self,
            "UIBucket",
            bucket_name=f"socratic-bench-ui-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Origin Access Identity for CloudFront
        oai = cloudfront.OriginAccessIdentity(
            self,
            "UIOriginAccessIdentity",
            comment="OAI for Socratic Bench UI bucket"
        )

        # Grant CloudFront read access to bucket
        ui_bucket.grant_read(oai)

        # CloudFront distribution
        distribution = cloudfront.Distribution(
            self,
            "UIDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    ui_bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                )
            ],
        )

        # Deploy UI assets
        s3deploy.BucketDeployment(
            self,
            "DeployUI",
            sources=[s3deploy.Source.asset("../ui")],
            destination_bucket=ui_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        # ========================================
        # Outputs
        # ========================================

        from aws_cdk import CfnOutput

        CfnOutput(self, "TableName", value=self.table.table_name)
        CfnOutput(self, "BucketName", value=self.data_bucket.bucket_name)
        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "ApiKeyId", value=api_key.key_id)
        CfnOutput(self, "UIUrl", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "EventBusName", value=self.event_bus.event_bus_name)
