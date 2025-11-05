#!/bin/bash
# Deploy Socratic Bench serverless infrastructure

set -e

echo "🚀 Deploying Socratic Bench Serverless..."

# Check prerequisites
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK not found. Install with: npm install -g aws-cdk"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found."
    exit 1
fi

# Navigate to infra directory
cd "$(dirname "$0")/../infra"

# Install CDK dependencies
echo "📦 Installing CDK dependencies..."
pip install -q -r requirements.txt

# Synthesize stack
echo "🔨 Synthesizing CloudFormation template..."
cdk synth

# Deploy
echo "☁️  Deploying to AWS..."
cdk deploy --require-approval never

# Get outputs
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

# Save outputs to file
aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs' \
  --output json > ../outputs.json

echo ""
echo "📝 Outputs saved to: serverless/outputs.json"
echo ""
echo "Next steps:"
echo "1. Upload config: ./scripts/upload-config.sh"
echo "2. Update UI: ./scripts/update-ui.sh"
echo "3. Test manually: ./scripts/test-run.sh"
