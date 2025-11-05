import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

export class SocraticBenchmarksStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ===================
    // 1. DynamoDB Table
    // ===================

    const table = new dynamodb.Table(this, 'SocraticBenchmarks', {
      tableName: 'SocraticBenchmarks',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST, // On-demand for low/variable traffic
      pointInTimeRecovery: true, // Backups
      removalPolicy: cdk.RemovalPolicy.RETAIN, // Don't delete data on stack delete
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES, // For real-time aggregation
    });

    // GSI1: Query by Model
    table.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2: Query by Vector (Elenchus/Maieutics/Aporia)
    table.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: { name: 'GSI2PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI2SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI3: Query by Manifest (reproducibility)
    table.addGlobalSecondaryIndex({
      indexName: 'GSI3',
      partitionKey: { name: 'GSI3PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI3SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // ===================
    // 2. S3 Bucket
    // ===================

    const bucket = new s3.Bucket(this, 'SocraticBenchBucket', {
      bucketName: `socratic-bench-${this.account}`,
      versioned: true, // Version control for immutability
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN, // Don't delete data
      lifecycleRules: [
        {
          id: 'ArchiveRawAfter90Days',
          prefix: 'raw/',
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(90),
            },
          ],
        },
      ],
    });

    // ===================
    // 3. SQS Queues
    // ===================

    // Dialogue Jobs Queue (model testing)
    const dialogueQueue = new sqs.Queue(this, 'DialogueJobsQueue', {
      queueName: 'dialogue-jobs',
      visibilityTimeout: cdk.Duration.seconds(300), // 5 minutes for long-running tests
      retentionPeriod: cdk.Duration.days(7),
      deadLetterQueue: {
        queue: new sqs.Queue(this, 'DialogueJobsDLQ', {
          queueName: 'dialogue-jobs-dlq',
        }),
        maxReceiveCount: 3, // Retry 3 times before DLQ
      },
    });

    // Judge Jobs Queue (evaluation)
    const judgeQueue = new sqs.Queue(this, 'JudgeJobsQueue', {
      queueName: 'judge-jobs',
      visibilityTimeout: cdk.Duration.seconds(120), // 2 minutes for judge calls
      retentionPeriod: cdk.Duration.days(7),
      deadLetterQueue: {
        queue: new sqs.Queue(this, 'JudgeJobsDLQ', {
          queueName: 'judge-jobs-dlq',
        }),
        maxReceiveCount: 3,
      },
    });

    // Curation Events (EventBridge custom bus)
    const curationBus = new events.EventBus(this, 'CurationEventBus', {
      eventBusName: 'curation-events',
    });

    // ===================
    // 4. IAM Roles
    // ===================

    // Common policy for DynamoDB + S3 + Bedrock
    const lambdaExecutionRole = new iam.Role(this, 'BenchmarkLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('AWSXRayDaemonWriteAccess'),
      ],
      inlinePolicies: {
        BenchmarkPermissions: new iam.PolicyDocument({
          statements: [
            // DynamoDB full access to table
            new iam.PolicyStatement({
              actions: [
                'dynamodb:PutItem',
                'dynamodb:GetItem',
                'dynamodb:UpdateItem',
                'dynamodb:Query',
                'dynamodb:Scan',
                'dynamodb:BatchGetItem',
                'dynamodb:BatchWriteItem',
              ],
              resources: [
                table.tableArn,
                `${table.tableArn}/index/*`,
              ],
            }),
            // S3 full access to bucket
            new iam.PolicyStatement({
              actions: [
                's3:PutObject',
                's3:GetObject',
                's3:DeleteObject',
                's3:ListBucket',
              ],
              resources: [
                bucket.bucketArn,
                `${bucket.bucketArn}/*`,
              ],
            }),
            // Bedrock access for Claude models
            new iam.PolicyStatement({
              actions: [
                'bedrock:InvokeModel',
                'bedrock:InvokeModelWithResponseStream',
              ],
              resources: [
                `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-*`,
              ],
            }),
            // EventBridge for curation events
            new iam.PolicyStatement({
              actions: ['events:PutEvents'],
              resources: [curationBus.eventBusArn],
            }),
            // SQS for queueing jobs
            new iam.PolicyStatement({
              actions: [
                'sqs:SendMessage',
                'sqs:ReceiveMessage',
                'sqs:DeleteMessage',
                'sqs:GetQueueAttributes',
              ],
              resources: [
                dialogueQueue.queueArn,
                judgeQueue.queueArn,
              ],
            }),
          ],
        }),
      },
    });

    // ===================
    // 5. Lambda Functions
    // ===================

    // Common Lambda properties
    const commonLambdaProps = {
      runtime: lambda.Runtime.PYTHON_3_12,
      role: lambdaExecutionRole,
      timeout: cdk.Duration.seconds(300),
      memorySize: 512,
      environment: {
        TABLE_NAME: table.tableName,
        BUCKET_NAME: bucket.bucketName,
        DIALOGUE_QUEUE_URL: dialogueQueue.queueUrl,
        JUDGE_QUEUE_URL: judgeQueue.queueUrl,
        EVENT_BUS_NAME: curationBus.eventBusName,
      },
      tracing: lambda.Tracing.ACTIVE, // X-Ray tracing
    };

    // Planner Lambda (creates manifests and queues jobs)
    const plannerLambda = new lambda.Function(this, 'PlannerLambda', {
      ...commonLambdaProps,
      functionName: 'socratic-bench-planner',
      code: lambda.Code.fromAsset('../lambdas/planner'),
      handler: 'index.handler',
      description: 'Creates benchmark manifests and enqueues dialogue jobs',
    });

    // Dialogue Runner Lambda (runs model tests)
    const dialogueLambda = new lambda.Function(this, 'DialogueLambda', {
      ...commonLambdaProps,
      functionName: 'socratic-bench-dialogue',
      code: lambda.Code.fromAsset('../lambdas/dialogue'),
      handler: 'index.handler',
      description: 'Runs Socratic dialogue tests and stores turns',
    });

    // Add SQS trigger for dialogue Lambda
    dialogueLambda.addEventSource(new SqsEventSource(dialogueQueue, {
      batchSize: 1, // Process one run at a time
      maxBatchingWindow: cdk.Duration.seconds(0),
    }));

    // Judge Runner Lambda (evaluates turns)
    const judgeLambda = new lambda.Function(this, 'JudgeLambda', {
      ...commonLambdaProps,
      functionName: 'socratic-bench-judge',
      code: lambda.Code.fromAsset('../lambdas/judge'),
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(120),
      description: 'Evaluates Socratic turns using judge model',
    });

    // Add SQS trigger for judge Lambda
    judgeLambda.addEventSource(new SqsEventSource(judgeQueue, {
      batchSize: 5, // Process multiple judges in parallel
      maxBatchingWindow: cdk.Duration.seconds(5),
    }));

    // Curator Lambda (aggregates results)
    const curatorLambda = new lambda.Function(this, 'CuratorLambda', {
      ...commonLambdaProps,
      functionName: 'socratic-bench-curator',
      code: lambda.Code.fromAsset('../lambdas/curator'),
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(60),
      description: 'Aggregates judge results and creates summaries',
    });

    // Add EventBridge trigger for curator Lambda
    const curationRule = new events.Rule(this, 'CurationRule', {
      eventBus: curationBus,
      eventPattern: {
        detailType: ['RunCompleted'],
      },
    });
    curationRule.addTarget(new targets.LambdaFunction(curatorLambda));

    // ===================
    // 6. API Gateway
    // ===================

    const api = new apigateway.RestApi(this, 'SocraticBenchApi', {
      restApiName: 'Socratic Benchmarks API',
      description: 'Admin API for benchmark management',
      deployOptions: {
        stageName: 'v1',
        tracingEnabled: true, // X-Ray
        metricsEnabled: true,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    // API Key for simple auth (can upgrade to Cognito later)
    const apiKey = api.addApiKey('ApiKey', {
      apiKeyName: 'socratic-bench-key',
      description: 'API key for benchmark admin operations',
    });

    const usagePlan = api.addUsagePlan('UsagePlan', {
      name: 'Standard',
      throttle: {
        rateLimit: 10,
        burstLimit: 20,
      },
    });
    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({ stage: api.deploymentStage });

    // Endpoints
    const manifests = api.root.addResource('manifests');
    manifests.addMethod('POST', new apigateway.LambdaIntegration(plannerLambda), {
      apiKeyRequired: true,
    });

    const runs = api.root.addResource('runs');
    runs.addMethod('GET', new apigateway.LambdaIntegration(plannerLambda), {
      apiKeyRequired: true,
    });

    const runDetail = runs.addResource('{run_id}');
    runDetail.addMethod('GET', new apigateway.LambdaIntegration(plannerLambda), {
      apiKeyRequired: true,
    });

    // ===================
    // 7. Outputs
    // ===================

    new cdk.CfnOutput(this, 'TableName', {
      value: table.tableName,
      description: 'DynamoDB table name',
      exportName: 'SocraticBenchmarksTableName',
    });

    new cdk.CfnOutput(this, 'BucketName', {
      value: bucket.bucketName,
      description: 'S3 bucket name',
      exportName: 'SocraticBenchmarksBucketName',
    });

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'API Gateway URL',
      exportName: 'SocraticBenchmarksApiUrl',
    });

    new cdk.CfnOutput(this, 'ApiKeyId', {
      value: apiKey.keyId,
      description: 'API Key ID (retrieve value from console)',
      exportName: 'SocraticBenchmarksApiKeyId',
    });
  }
}
