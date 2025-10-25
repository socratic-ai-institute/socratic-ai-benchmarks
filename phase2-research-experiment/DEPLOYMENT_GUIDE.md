# Socratic Dashboard Deployment Guide

## Quick Start (5-Minute Deploy)

```bash
# 1. Clone repository
git clone https://github.com/your-org/socratic-dashboard.git
cd socratic-dashboard

# 2. Install dependencies
npm install

# 3. Configure AWS credentials
aws configure

# 4. Deploy infrastructure (CDK)
cd infrastructure
npm install
cdk bootstrap  # First time only
cdk deploy DashboardStack

# 5. Configure Amplify
cd ..
amplify init
amplify push

# 6. Deploy frontend
git push origin main  # Auto-deploys via Amplify Console
```

Your dashboard will be live at: `https://main.xxxxx.amplifyapp.com`

---

## Detailed Setup Instructions

### Prerequisites

**Required Software:**
- Node.js 18+ (`node --version`)
- AWS CLI 2.x (`aws --version`)
- Git (`git --version`)
- npm or yarn

**AWS Account Requirements:**
- Administrator access (or permissions for: Amplify, Cognito, AppSync, DynamoDB, Lambda, S3, CloudWatch)
- Credit card on file (uses AWS Free Tier where possible)

**Estimated Costs:**
- Development: ~$5/month
- Production: ~$37/month (based on 1000 sessions/month)

---

## Part 1: Infrastructure Deployment (AWS CDK)

### 1.1 Install AWS CDK

```bash
npm install -g aws-cdk

# Verify installation
cdk --version
# Should show: 2.x.x or higher
```

### 1.2 Configure AWS Credentials

**Option A: AWS CLI**
```bash
aws configure
# AWS Access Key ID: [your key]
# AWS Secret Access Key: [your secret]
# Default region: us-east-1
# Default output format: json
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option C: AWS SSO**
```bash
aws sso login --profile socratic-research
export AWS_PROFILE=socratic-research
```

### 1.3 Initialize CDK Project

```bash
cd infrastructure

# Install dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/us-east-1

# Expected output:
# ✅  Environment aws://123456789012/us-east-1 bootstrapped
```

### 1.4 Deploy Stack

```bash
# Synthesize CloudFormation template (preview)
cdk synth

# Deploy to AWS
cdk deploy DashboardStack

# Confirm when prompted:
# Do you wish to deploy these changes (y/n)? y
```

**Deployment takes ~5-10 minutes**

Expected output:
```
✅  DashboardStack

Outputs:
DashboardStack.UserPoolId = us-east-1_xxxxx
DashboardStack.GraphQLEndpoint = https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql
DashboardStack.AmplifyAppId = dxxxxx
```

**Save these outputs** – you'll need them for frontend configuration.

### 1.5 Verify Infrastructure

```bash
# Check Cognito User Pool
aws cognito-idp describe-user-pool --user-pool-id us-east-1_xxxxx

# Check AppSync API
aws appsync get-graphql-api --api-id xxxxx

# Check DynamoDB tables
aws dynamodb list-tables
# Should show: socratic-sessions, socratic-students, etc.
```

---

## Part 2: Frontend Setup (React + Amplify)

### 2.1 Initialize Frontend Project

```bash
cd ../frontend  # From repository root

# Install dependencies
npm install

# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
amplify init

# Prompts:
? Enter a name for the project: socraticDashboard
? Enter a name for the environment: dev
? Choose your default editor: Visual Studio Code
? Choose the type of app: javascript
? What javascript framework: react
? Source Directory Path: src
? Distribution Directory Path: dist
? Build Command: npm run build
? Start Command: npm run dev
```

### 2.2 Configure Amplify Backend

**Option A: Link to Existing Infrastructure (Recommended)**

```bash
# Use outputs from CDK deployment
amplify import auth

# Select: Cognito User Pool
# Enter User Pool ID: us-east-1_xxxxx (from CDK output)
# Enter User Pool Client ID: [from CDK output]

amplify import api

# Select: GraphQL (AppSync)
# Enter GraphQL endpoint: https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql
# Enter API ID: xxxxx
```

**Option B: Manual Configuration**

Create `src/aws-exports.js`:

```javascript
const awsconfig = {
  aws_project_region: 'us-east-1',
  aws_cognito_region: 'us-east-1',
  aws_user_pools_id: 'us-east-1_xxxxx',
  aws_user_pools_web_client_id: 'xxxxx',
  aws_appsync_graphqlEndpoint: 'https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql',
  aws_appsync_region: 'us-east-1',
  aws_appsync_authenticationType: 'AMAZON_COGNITO_USER_POOLS',
};

export default awsconfig;
```

### 2.3 Configure Environment Variables

Create `.env.local`:

```bash
# AWS Configuration
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxx
VITE_COGNITO_CLIENT_ID=xxxxx
VITE_APPSYNC_ENDPOINT=https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql

# Mapbox (for live monitoring map)
VITE_MAPBOX_TOKEN=pk.your_mapbox_token

# Feature Flags
VITE_ENABLE_LIVE_MONITORING=true
VITE_ENABLE_EXPORT=true

# Analytics (optional)
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

**Get Mapbox Token:**
1. Sign up at https://mapbox.com
2. Create access token
3. Copy token to `.env.local`

### 2.4 Generate GraphQL Types

```bash
# Download schema from AppSync
amplify codegen

# Or manually:
npm run codegen

# Generates: src/types/graphql.ts
```

Verify `codegen.yml`:

```yaml
overwrite: true
schema:
  - https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql
documents: 'src/**/*.tsx'
generates:
  src/types/graphql.ts:
    plugins:
      - typescript
      - typescript-operations
      - typescript-react-query
    config:
      withHooks: true
      withComponent: false
```

### 2.5 Test Locally

```bash
# Start dev server
npm run dev

# Opens browser at http://localhost:5173

# Login with test credentials (see "Creating Users" section below)
```

---

## Part 3: Amplify Hosting Deployment

### 3.1 Connect GitHub Repository

**Via AWS Console:**

1. Go to AWS Amplify Console: https://console.aws.amazon.com/amplify
2. Click "New app" → "Host web app"
3. Select "GitHub"
4. Authorize AWS Amplify
5. Select repository: `your-org/socratic-dashboard`
6. Select branch: `main`

**Or via CLI:**

```bash
amplify add hosting

? Select the plugin module to execute: Hosting with Amplify Console
? Choose a type: Continuous deployment (Git-based deployments)
```

### 3.2 Configure Build Settings

Edit `amplify.yml` (in repository root):

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
        - npm run codegen  # Generate GraphQL types
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*

# Performance optimizations
customHeaders:
  - pattern: '**/*.js'
    headers:
      - key: Cache-Control
        value: 'public, max-age=31536000, immutable'
  - pattern: '**/*.css'
    headers:
      - key: Cache-Control
        value: 'public, max-age=31536000, immutable'
  - pattern: '**/*.html'
    headers:
      - key: Cache-Control
        value: 'no-cache, no-store, must-revalidate'
  - pattern: '**'
    headers:
      - key: Strict-Transport-Security
        value: 'max-age=31536000; includeSubDomains'
      - key: X-Frame-Options
        value: 'DENY'
      - key: X-Content-Type-Options
        value: 'nosniff'
```

### 3.3 Set Environment Variables in Amplify

**Via AWS Console:**

1. Amplify Console → Your App → "Environment variables"
2. Add variables:

| Key | Value |
|-----|-------|
| `VITE_AWS_REGION` | `us-east-1` |
| `VITE_COGNITO_USER_POOL_ID` | `us-east-1_xxxxx` |
| `VITE_COGNITO_CLIENT_ID` | `xxxxx` |
| `VITE_APPSYNC_ENDPOINT` | `https://xxxxx...` |
| `VITE_MAPBOX_TOKEN` | `pk.xxxxx` |

**Or via CLI:**

```bash
amplify env add

? Enter a name for the environment: prod
? Do you want to use an AWS profile? Yes
? Please choose the profile: default

amplify push
```

### 3.4 Deploy to Amplify

**Option A: Git Push (Automatic)**

```bash
git add .
git commit -m "Initial dashboard deployment"
git push origin main

# Amplify automatically detects push and starts build
```

**Option B: Manual Deploy**

```bash
amplify publish

# Builds and deploys to Amplify hosting
```

**Build Progress:**

```
Provision
├─ ✅ Downloading source code
├─ ✅ Installing dependencies (2m 30s)
└─ ✅ Building application (3m 15s)

Deploy
├─ ✅ Uploading artifacts
└─ ✅ Deploying to CDN

✅ Deployment complete!
URL: https://main.dxxxxx.amplifyapp.com
```

### 3.5 Set Up Branch Deployments

**Main Branch (Production):**
- URL: `https://main.dxxxxx.amplifyapp.com`
- Auto-deploy on push to `main`
- Connected to production backend

**Staging Branch:**

```bash
# Create staging branch
git checkout -b staging
git push origin staging

# In Amplify Console:
# 1. Go to "Branches"
# 2. Click "Connect branch"
# 3. Select "staging"
# 4. Configure environment variables (staging values)
```

**Preview Deployments (for PRs):**

1. Amplify Console → "Previews"
2. Enable "Pull request previews"
3. Select: "Automatically deploy pull requests"

Now every PR gets a preview URL:
`https://pr-123.dxxxxx.amplifyapp.com`

---

## Part 4: Custom Domain Setup

### 4.1 Purchase Domain (if needed)

**Option A: Route 53**
```bash
aws route53domains register-domain --domain-name socraticresearch.org
```

**Option B: External Registrar** (GoDaddy, Namecheap, etc.)

### 4.2 Configure Domain in Amplify

**Via AWS Console:**

1. Amplify Console → Your App → "Domain management"
2. Click "Add domain"
3. Enter domain: `socraticresearch.org`
4. Configure subdomains:
   - `dashboard.socraticresearch.org` → main branch
   - `staging.socraticresearch.org` → staging branch
5. Click "Configure domain"

**Amplify creates:**
- SSL certificate (via AWS Certificate Manager)
- CNAME records (automatic if using Route 53)

### 4.3 Manual DNS Configuration (if not using Route 53)

Add these CNAME records to your DNS provider:

| Type | Name | Value |
|------|------|-------|
| CNAME | `dashboard` | `main.dxxxxx.amplifyapp.com` |
| CNAME | `staging` | `staging.dxxxxx.amplifyapp.com` |

**Wait 5-60 minutes for DNS propagation**

Verify:
```bash
dig dashboard.socraticresearch.org
# Should resolve to Amplify CDN
```

### 4.4 Enable HTTPS (Automatic)

Amplify automatically:
- Requests SSL certificate from ACM
- Validates domain ownership
- Configures HTTPS redirects

**Wait 15-30 minutes for certificate issuance**

Verify:
```bash
curl -I https://dashboard.socraticresearch.org
# Should show: HTTP/2 200
# Strict-Transport-Security header present
```

---

## Part 5: User Management (Cognito)

### 5.1 Create Administrator User

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_xxxxx \
  --username admin@university.edu \
  --user-attributes Name=email,Value=admin@university.edu \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

# Add to Administrators group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id us-east-1_xxxxx \
  --username admin@university.edu \
  --group-name Administrators
```

**User will be prompted to change password on first login**

### 5.2 Create Researcher Users (Bulk)

Create `users.csv`:
```csv
email,group
researcher1@university.edu,Researchers
researcher2@university.edu,Researchers
pi@university.edu,PIs
```

Run script:
```bash
#!/bin/bash
while IFS=, read -r email group; do
  if [ "$email" != "email" ]; then  # Skip header
    aws cognito-idp admin-create-user \
      --user-pool-id us-east-1_xxxxx \
      --username "$email" \
      --user-attributes Name=email,Value="$email" \
      --temporary-password "Welcome2024!" \
      --message-action SUPPRESS

    aws cognito-idp admin-add-user-to-group \
      --user-pool-id us-east-1_xxxxx \
      --username "$email" \
      --group-name "$group"

    echo "Created user: $email (group: $group)"
  fi
done < users.csv
```

### 5.3 Configure MFA (Optional but Recommended)

**Enable MFA for Administrators:**

```bash
aws cognito-idp set-user-pool-mfa-config \
  --user-pool-id us-east-1_xxxxx \
  --software-token-mfa-configuration Enabled=true \
  --mfa-configuration OPTIONAL
```

**Enforce MFA for specific group:**

1. Go to Cognito Console → User Pool → "Groups"
2. Select "Administrators"
3. Edit → Set precedence to enforce MFA

### 5.4 Reset User Password (if needed)

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_xxxxx \
  --username researcher@university.edu \
  --password "NewSecurePass123!" \
  --permanent
```

---

## Part 6: Monitoring & Logging

### 6.1 Enable CloudWatch Logs

**AppSync Logs:**
```bash
aws appsync update-graphql-api \
  --api-id xxxxx \
  --log-config \
    fieldLogLevel=ERROR,\
    cloudWatchLogsRoleArn=arn:aws:iam::ACCOUNT-ID:role/AppSyncLogsRole
```

**Lambda Logs:**
Automatically enabled. View at:
```bash
aws logs tail /aws/lambda/DashboardStack-AggregateMetricsResolver --follow
```

### 6.2 Set Up Alarms

**High Error Rate Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name socratic-dashboard-high-errors \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/AppSync \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT-ID:dashboard-alerts
```

**DynamoDB Throttling Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name socratic-dashboard-throttling \
  --metric-name UserErrors \
  --namespace AWS/DynamoDB \
  --dimensions Name=TableName,Value=socratic-sessions \
  --statistic Sum \
  --period 60 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### 6.3 View Metrics

**Via AWS Console:**

1. CloudWatch → Dashboards
2. Create custom dashboard: "Socratic Research"
3. Add widgets:
   - AppSync request count
   - Lambda invocations
   - DynamoDB read/write capacity
   - Amplify deployment status

**Via CLI:**
```bash
# AppSync requests (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppSync \
  --metric-name 4XXError \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### 6.4 Enable X-Ray Tracing

**For Lambda:**
```typescript
// In CDK stack
import * as lambda from 'aws-cdk-lib/aws-lambda';

const resolver = new lambda.Function(this, 'Resolver', {
  // ... other config
  tracing: lambda.Tracing.ACTIVE,
});
```

**For AppSync:**
```bash
aws appsync update-graphql-api \
  --api-id xxxxx \
  --xray-enabled
```

View traces:
```bash
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s)
```

---

## Part 7: Backup & Disaster Recovery

### 7.1 Enable DynamoDB Backups

**Point-in-Time Recovery:**
```bash
aws dynamodb update-continuous-backups \
  --table-name socratic-sessions \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

**Scheduled Backups:**
```bash
# Create backup plan
aws backup create-backup-plan \
  --backup-plan '{
    "BackupPlanName": "SocraticDailyBackup",
    "Rules": [{
      "RuleName": "DailyBackup",
      "TargetBackupVaultName": "Default",
      "ScheduleExpression": "cron(0 5 * * ? *)",
      "StartWindowMinutes": 60,
      "CompletionWindowMinutes": 120,
      "Lifecycle": {
        "DeleteAfterDays": 30
      }
    }]
  }'

# Assign resources to backup plan
aws backup create-backup-selection \
  --backup-plan-id [plan-id] \
  --backup-selection '{
    "SelectionName": "SocraticTables",
    "IamRoleArn": "arn:aws:iam::ACCOUNT-ID:role/AWSBackupRole",
    "Resources": [
      "arn:aws:dynamodb:us-east-1:ACCOUNT-ID:table/socratic-sessions",
      "arn:aws:dynamodb:us-east-1:ACCOUNT-ID:table/socratic-students"
    ]
  }'
```

### 7.2 Restore from Backup

**Restore entire table:**
```bash
aws dynamodb restore-table-from-backup \
  --target-table-name socratic-sessions-restored \
  --backup-arn arn:aws:dynamodb:us-east-1:ACCOUNT-ID:table/socratic-sessions/backup/xxxxx
```

**Restore to point in time:**
```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name socratic-sessions \
  --target-table-name socratic-sessions-restored \
  --restore-date-time 2025-10-23T14:00:00Z
```

### 7.3 Infrastructure as Code Backup

**Export CDK stack:**
```bash
cd infrastructure
cdk synth > cloudformation-template.yaml

# Commit to git
git add cloudformation-template.yaml
git commit -m "Backup: CDK template snapshot"
```

**Version control all config:**
```bash
git tag -a v1.0.0 -m "Production deployment snapshot"
git push origin v1.0.0
```

---

## Part 8: Performance Tuning

### 8.1 Optimize DynamoDB

**Create Global Secondary Indexes:**

```bash
# Index for querying by condition
aws dynamodb update-table \
  --table-name socratic-sessions \
  --attribute-definitions \
    AttributeName=conditionKey,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --global-secondary-index-updates '[{
    "Create": {
      "IndexName": "byCondition",
      "KeySchema": [
        {"AttributeName": "conditionKey", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"},
      "ProvisionedThroughput": {
        "ReadCapacityUnits": 5,
        "WriteCapacityUnits": 5
      }
    }
  }]'
```

**Enable Auto Scaling:**

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/socratic-sessions \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 5 \
  --max-capacity 100

aws application-autoscaling put-scaling-policy \
  --service-namespace dynamodb \
  --resource-id table/socratic-sessions \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --policy-name SocraticSessionsReadScaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "DynamoDBReadCapacityUtilization"
    }
  }'
```

### 8.2 Lambda Performance

**Increase Memory (faster execution):**

```typescript
// In CDK stack
const resolver = new lambda.Function(this, 'Resolver', {
  memorySize: 512,  // MB (default: 128)
  timeout: cdk.Duration.seconds(30),  // Prevent timeouts
});
```

**Enable Provisioned Concurrency (eliminate cold starts):**

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name DashboardStack-AggregateMetricsResolver \
  --provisioned-concurrent-executions 2
```

### 8.3 AppSync Caching

**Enable API-level caching:**

```bash
aws appsync create-api-cache \
  --api-id xxxxx \
  --ttl 300 \
  --api-caching-behavior PER_RESOLVER_CACHING \
  --type T2_SMALL
```

**Configure per-resolver caching:**

In AppSync Console:
1. Schema → Resolvers → `listSessions`
2. Enable caching → TTL: 60 seconds
3. Caching keys: `$context.arguments`

### 8.4 Amplify CDN Optimization

**Aggressive caching for static assets:**

Already configured in `amplify.yml` (see Part 3).

**Verify cache headers:**
```bash
curl -I https://dashboard.socraticresearch.org/assets/index-abc123.js
# Should show: Cache-Control: public, max-age=31536000, immutable
```

---

## Part 9: Security Hardening

### 9.1 Enable AWS WAF

**Create Web ACL:**

```bash
aws wafv2 create-web-acl \
  --name socratic-dashboard-waf \
  --scope CLOUDFRONT \
  --default-action Allow={} \
  --rules '[
    {
      "Name": "RateLimitRule",
      "Priority": 1,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": {"Block": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimitRule"
      }
    },
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 2,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRuleSetMetric"
      }
    }
  ]' \
  --visibility-config \
    SampledRequestsEnabled=true,\
    CloudWatchMetricsEnabled=true,\
    MetricName=SocraticDashboardWAF
```

**Associate with Amplify:**
```bash
# Get Amplify CloudFront distribution ID
aws amplify get-app --app-id dxxxxx

# Associate WAF
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:us-east-1:ACCOUNT-ID:global/webacl/socratic-dashboard-waf/xxxxx \
  --resource-arn arn:aws:cloudfront::ACCOUNT-ID:distribution/E123456789
```

### 9.2 Secrets Management

**Store API keys in Secrets Manager:**

```bash
# Store Mapbox token
aws secretsmanager create-secret \
  --name socratic-dashboard/mapbox-token \
  --secret-string "pk.your_actual_token"

# Grant Lambda access
aws secretsmanager get-secret-value \
  --secret-id socratic-dashboard/mapbox-token
```

**Access in Lambda:**
```typescript
import { SecretsManager } from 'aws-sdk';

const secrets = new SecretsManager();

export async function handler(event: any) {
  const { SecretString } = await secrets.getSecretValue({
    SecretId: 'socratic-dashboard/mapbox-token'
  }).promise();

  const mapboxToken = SecretString;
  // Use token...
}
```

### 9.3 Audit Logging

**Enable CloudTrail:**

```bash
aws cloudtrail create-trail \
  --name socratic-dashboard-audit \
  --s3-bucket-name socratic-audit-logs-bucket \
  --is-multi-region-trail \
  --include-global-service-events

aws cloudtrail start-logging \
  --name socratic-dashboard-audit
```

**Log all Cognito events:**

```bash
aws logs create-log-group --log-group-name /aws/cognito/socratic-dashboard

aws cognito-idp update-user-pool \
  --user-pool-id us-east-1_xxxxx \
  --user-pool-add-ons AdvancedSecurityMode=ENFORCED
```

---

## Part 10: Troubleshooting

### Common Issues

#### Issue: "Unauthorized" errors in dashboard

**Symptom:** Login works, but all API calls return 401

**Solution:**
```bash
# Check if user is in correct group
aws cognito-idp admin-list-groups-for-user \
  --user-pool-id us-east-1_xxxxx \
  --username researcher@university.edu

# If empty, add to group:
aws cognito-idp admin-add-user-to-group \
  --user-pool-id us-east-1_xxxxx \
  --username researcher@university.edu \
  --group-name Researchers
```

#### Issue: Amplify build fails

**Symptom:** Build logs show `npm ERR! code ELIFECYCLE`

**Solution:**
1. Check `amplify.yml` build commands
2. Verify environment variables are set
3. Test build locally:
   ```bash
   npm ci
   npm run build
   ```
4. Check Node version in `package.json`:
   ```json
   "engines": {
     "node": ">=18.0.0"
   }
   ```

#### Issue: GraphQL queries return null

**Symptom:** Data shows as `null` in dashboard

**Solution:**
```bash
# Check DynamoDB table
aws dynamodb scan --table-name socratic-sessions --limit 5

# Check AppSync resolver logs
aws logs tail /aws/appsync/apis/xxxxx --follow

# Test query directly in AppSync Console
# Queries → Run query with test JWT token
```

#### Issue: Real-time subscriptions not working

**Symptom:** Live monitoring doesn't update

**Solution:**
1. Verify WebSocket connection in browser DevTools → Network → WS
2. Check subscription permissions in AppSync schema
3. Ensure DynamoDB Streams enabled:
   ```bash
   aws dynamodb describe-table --table-name socratic-sessions
   # Look for: "StreamSpecification": { "StreamEnabled": true }
   ```

---

## Part 11: Production Checklist

Before going live:

- [ ] **Infrastructure**
  - [ ] CDK stack deployed successfully
  - [ ] All DynamoDB tables created with indexes
  - [ ] AppSync API functional
  - [ ] Lambda resolvers tested

- [ ] **Frontend**
  - [ ] Amplify hosting configured
  - [ ] Custom domain set up
  - [ ] SSL certificate issued
  - [ ] Environment variables configured

- [ ] **Security**
  - [ ] Cognito users created
  - [ ] MFA enabled for admins
  - [ ] WAF rules configured
  - [ ] Secrets in Secrets Manager (not env vars)
  - [ ] CloudTrail logging enabled

- [ ] **Monitoring**
  - [ ] CloudWatch alarms configured
  - [ ] SNS notification topic created
  - [ ] X-Ray tracing enabled
  - [ ] Error tracking set up

- [ ] **Backups**
  - [ ] DynamoDB point-in-time recovery enabled
  - [ ] Scheduled backups configured
  - [ ] Tested restore procedure

- [ ] **Performance**
  - [ ] DynamoDB auto-scaling configured
  - [ ] Lambda provisioned concurrency (if needed)
  - [ ] AppSync caching enabled
  - [ ] CDN cache headers verified

- [ ] **Testing**
  - [ ] Login flow tested
  - [ ] All dashboard views functional
  - [ ] Export feature working
  - [ ] Real-time updates working
  - [ ] Mobile responsiveness checked

- [ ] **Documentation**
  - [ ] User guide written
  - [ ] Admin documentation complete
  - [ ] Runbook for common issues
  - [ ] Contact info for support

---

## Part 12: Rollback Procedures

### Rollback Frontend Deployment

**Via Amplify Console:**
1. Go to Amplify Console → App → "Deployments"
2. Find previous successful deployment
3. Click "Redeploy this version"

**Via CLI:**
```bash
# Get deployment history
aws amplify list-jobs --app-id dxxxxx --branch-name main

# Redeploy specific version
git revert HEAD
git push origin main
```

### Rollback Infrastructure Changes

**Via CDK:**
```bash
cd infrastructure

# Revert to previous commit
git log --oneline  # Find previous commit hash
git checkout abc123 -- lib/dashboard-stack.ts

# Redeploy
cdk deploy DashboardStack
```

**Via CloudFormation Console:**
1. Go to CloudFormation → Stacks → DashboardStack
2. Click "Stack actions" → "Rollback stack"
3. Select previous version

### Emergency Maintenance Mode

**Disable dashboard temporarily:**

```bash
# Update Amplify app to show maintenance page
cat > maintenance.html <<EOF
<!DOCTYPE html>
<html>
<head><title>Maintenance</title></head>
<body>
  <h1>Dashboard Under Maintenance</h1>
  <p>We'll be back shortly. Check back in 30 minutes.</p>
</body>
</html>
EOF

# Deploy maintenance page
aws amplify start-deployment \
  --app-id dxxxxx \
  --branch-name main \
  --source-url s3://maintenance-bucket/maintenance.html
```

---

## Support & Resources

**Documentation:**
- AWS Amplify: https://docs.amplify.aws
- AWS AppSync: https://docs.aws.amazon.com/appsync
- React Query: https://tanstack.com/query/latest

**Community:**
- GitHub Issues: https://github.com/your-org/socratic-dashboard/issues
- Slack: #socratic-research-tech

**AWS Support:**
- Support Center: https://console.aws.amazon.com/support
- Support Plan: Developer (recommended) or Business

**Emergency Contacts:**
- Tech Lead: tech-lead@university.edu
- AWS Account Manager: [if applicable]

---

## Next Steps

After deployment:

1. **Create test data** (see Student App documentation)
2. **Train researchers** on dashboard usage
3. **Monitor for 1 week** before full rollout
4. **Collect feedback** and iterate
5. **Plan for scale** (increase DynamoDB capacity as needed)

**Congratulations! Your dashboard is now live.** 🎉
