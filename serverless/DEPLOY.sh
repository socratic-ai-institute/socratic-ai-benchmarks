#!/bin/bash
#
# Complete deployment script for Socratic AI Benchmarking Platform
# Deploys: CDK infrastructure, configuration, dashboard, cost monitoring
#
# Usage: ./DEPLOY.sh
#
# Prerequisites:
# - AWS CLI configured with 'mvp' profile
# - AWS CDK installed (npm install -g aws-cdk)
# - Python 3.12+
# - Node.js 20+

set -e  # Exit on error

echo "=========================================="
echo "Socratic AI Benchmarking Platform"
echo "Cloud Deployment Script"
echo "=========================================="
echo ""

# Configuration
export AWS_PROFILE=mvp
export AWS_REGION=us-east-1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function log_error() {
    echo -e "${RED}❌ $1${NC}"
}

function log_info() {
    echo -e "ℹ️  $1"
}

# Phase 1: Prerequisites Check
echo ""
echo "Phase 1: Checking Prerequisites..."
echo "-----------------------------------"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install: https://aws.amazon.com/cli/"
    exit 1
fi
log_success "AWS CLI found: $(aws --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found"
    exit 1
fi
log_success "Python found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js not found"
    exit 1
fi
log_success "Node.js found: $(node --version)"

# Check CDK
if ! command -v cdk &> /dev/null; then
    log_error "AWS CDK not found. Install with: npm install -g aws-cdk"
    exit 1
fi
log_success "AWS CDK found: $(cdk --version)"

# Check AWS credentials
if ! aws sts get-caller-identity --profile $AWS_PROFILE &> /dev/null; then
    log_error "AWS credentials not configured for profile: $AWS_PROFILE"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query 'Account' --output text)
log_success "AWS credentials valid (Account: $ACCOUNT_ID)"

# Check Bedrock access
if ! aws bedrock list-foundation-models --region $AWS_REGION --profile $AWS_PROFILE --query 'modelSummaries[0].modelId' --output text &> /dev/null; then
    log_warning "Bedrock access not verified - you may need to request model access in AWS Console"
else
    log_success "Bedrock access verified"
fi

# Phase 2: Install Dependencies
echo ""
echo "Phase 2: Installing Dependencies..."
echo "-----------------------------------"

cd infra
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
log_info "Installing CDK dependencies..."
pip install -q -r requirements.txt
log_success "CDK dependencies installed"

# Phase 3: Bootstrap CDK (if needed)
echo ""
echo "Phase 3: CDK Bootstrap..."
echo "-------------------------"

if aws cloudformation describe-stacks --stack-name CDKToolkit --profile $AWS_PROFILE &> /dev/null; then
    log_success "CDK already bootstrapped"
else
    log_info "Bootstrapping CDK (first-time setup)..."
    cdk bootstrap --profile $AWS_PROFILE
    log_success "CDK bootstrap complete"
fi

# Phase 4: Deploy Infrastructure
echo ""
echo "Phase 4: Deploying CDK Infrastructure..."
echo "----------------------------------------"
log_info "This will create:"
log_info "  - 5 Lambda functions (Planner, Runner, Judge, Curator, API)"
log_info "  - 2 SQS queues + DLQs"
log_info "  - 1 DynamoDB table with 2 GSIs"
log_info "  - 2 S3 buckets (data + UI)"
log_info "  - 1 EventBridge rule (weekly cron)"
log_info "  - 1 API Gateway with API key"
log_info "  - 1 CloudFront distribution"
echo ""
read -p "Deploy infrastructure? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_error "Deployment cancelled"
    exit 1
fi

log_info "Deploying CDK stack (this may take 10-15 minutes)..."
cdk deploy --require-approval never --profile $AWS_PROFILE

log_success "Infrastructure deployed!"

# Phase 5: Extract Outputs
echo ""
echo "Phase 5: Extracting Stack Outputs..."
echo "-------------------------------------"

DATA_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile $AWS_PROFILE \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text)

UI_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile $AWS_PROFILE \
  --query 'Stacks[0].Outputs[?OutputKey==`UIBucketName`].OutputValue' \
  --output text)

API_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile $AWS_PROFILE \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile $AWS_PROFILE \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
  --output text)

API_KEY=$(aws apigateway get-api-key \
  --api-key $API_KEY_ID \
  --include-value \
  --profile $AWS_PROFILE \
  --query 'value' \
  --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile $AWS_PROFILE \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text)

log_success "Stack outputs extracted"
log_info "Data Bucket: $DATA_BUCKET"
log_info "UI Bucket: $UI_BUCKET"
log_info "API URL: $API_URL"
log_info "CloudFront URL: $CLOUDFRONT_URL"

# Phase 6: Upload Configuration
echo ""
echo "Phase 6: Uploading Configuration..."
echo "------------------------------------"

cd "$SCRIPT_DIR"
log_info "Uploading config-24-models.json to S3..."
aws s3 cp config-24-models.json s3://$DATA_BUCKET/artifacts/config.json --profile $AWS_PROFILE
log_success "Configuration uploaded"

# Phase 7: Deploy Dashboard
echo ""
echo "Phase 7: Deploying Dashboard to CloudFront..."
echo "----------------------------------------------"

# Copy comprehensive dashboard
log_info "Copying dashboard from Phase 1 results..."
cp ../../comprehensive_dashboard.html ui/index.html

# Update API endpoint in dashboard
log_info "Updating dashboard with API endpoint..."
sed -i.bak "s|YOUR_API_URL|$API_URL|g" ui/index.html
sed -i.bak "s|YOUR_API_KEY|$API_KEY|g" ui/index.html
rm ui/index.html.bak

# Upload to S3
log_info "Uploading dashboard to S3..."
aws s3 sync ui/ s3://$UI_BUCKET/ --profile $AWS_PROFILE --delete

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(aws cloudfront list-distributions --profile $AWS_PROFILE \
  --query "DistributionList.Items[?Origins.Items[?DomainName=='$UI_BUCKET.s3.amazonaws.com']].Id" \
  --output text)

if [ -n "$DISTRIBUTION_ID" ]; then
    log_info "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
      --distribution-id $DISTRIBUTION_ID \
      --paths "/*" \
      --profile $AWS_PROFILE > /dev/null
    log_success "CloudFront cache invalidated"
fi

log_success "Dashboard deployed!"

# Phase 8: Test Deployment
echo ""
echo "Phase 8: Testing Deployment..."
echo "-------------------------------"

log_info "Triggering test run..."
PLANNER_FUNCTION=$(aws lambda list-functions --profile $AWS_PROFILE \
  --query "Functions[?starts_with(FunctionName, 'SocraticBenchStack-PlannerFunction')].FunctionName" \
  --output text)

aws lambda invoke \
  --function-name $PLANNER_FUNCTION \
  --profile $AWS_PROFILE \
  --payload '{}' \
  /tmp/planner-response.json > /dev/null

MANIFEST_ID=$(cat /tmp/planner-response.json | python3 -c "import json, sys; print(json.load(sys.stdin).get('manifest_id', 'unknown'))")

if [ "$MANIFEST_ID" != "unknown" ]; then
    log_success "Test run triggered! Manifest ID: $MANIFEST_ID"
    log_info "Processing will take ~10-15 minutes..."
    log_info "Monitor progress: aws logs tail /aws/lambda/$PLANNER_FUNCTION --follow --profile $AWS_PROFILE"
else
    log_warning "Could not extract manifest ID from response"
fi

# Phase 9: Save Deployment Info
echo ""
echo "Phase 9: Saving Deployment Info..."
echo "-----------------------------------"

cat > DEPLOYMENT_INFO.txt << EOF
Socratic AI Benchmarking Platform - Deployment Info
====================================================

Deployed: $(date)
AWS Account: $ACCOUNT_ID
AWS Region: $AWS_REGION
AWS Profile: $AWS_PROFILE

Infrastructure:
- Stack Name: SocraticBenchStack
- Data Bucket: $DATA_BUCKET
- UI Bucket: $UI_BUCKET

API Access:
- API URL: $API_URL
- API Key: $API_KEY

Dashboard:
- CloudFront URL: $CLOUDFRONT_URL

Weekly Schedule:
- Day: Monday
- Time: 3:00 AM UTC
- EventBridge Rule: SocraticBenchStack-WeeklyTrigger

Cost Estimate:
- Weekly: ~\$5.50 (24 models, 2 scenarios)
- Monthly: ~\$22
- Savings vs 25 models: ~\$9/month (removed Claude 3 Opus)

Next Steps:
1. Visit dashboard: $CLOUDFRONT_URL
2. Wait ~15 minutes for first test run to complete
3. Monitor costs in CloudWatch
4. Review weekly results each Monday

Useful Commands:
================

# Trigger manual run
aws lambda invoke --function-name $PLANNER_FUNCTION --profile $AWS_PROFILE --payload '{}' /tmp/response.json

# Monitor logs
aws logs tail /aws/lambda/$PLANNER_FUNCTION --follow --profile $AWS_PROFILE

# Check SQS queue depth
aws sqs get-queue-attributes --queue-url \$(aws sqs get-queue-url --queue-name socratic-dialogue-jobs --profile $AWS_PROFILE --query 'QueueUrl' --output text) --attribute-names ApproximateNumberOfMessages --profile $AWS_PROFILE

# Update configuration
aws s3 cp config-24-models.json s3://$DATA_BUCKET/artifacts/config.json --profile $AWS_PROFILE

# Redeploy dashboard
aws s3 sync ui/ s3://$UI_BUCKET/ --profile $AWS_PROFILE --delete

# Cleanup (delete everything)
cd infra && cdk destroy --profile $AWS_PROFILE
EOF

log_success "Deployment info saved to: DEPLOYMENT_INFO.txt"

# Final Summary
echo ""
echo "=========================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
log_success "Dashboard URL: $CLOUDFRONT_URL"
log_info "First test run is processing (check in ~15 minutes)"
log_info "Weekly automated runs: Every Monday at 3:00 AM UTC"
log_info "Estimated cost: ~\$5.50/week or ~\$22/month"
echo ""
log_info "Deployment details saved to: DEPLOYMENT_INFO.txt"
echo ""
echo "=========================================="
