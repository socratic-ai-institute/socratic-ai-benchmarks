#!/bin/bash
# Upload default configuration to S3

set -e

echo "📤 Uploading default configuration..."

# Get bucket name from stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Could not find bucket name. Is the stack deployed?"
    exit 1
fi

# Create default config
cat > /tmp/socratic-config.json << 'EOF'
{
  "models": [
    {
      "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "provider": "anthropic",
      "temperature": 0.7,
      "max_tokens": 200
    },
    {
      "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
      "provider": "anthropic",
      "temperature": 0.7,
      "max_tokens": 200
    }
  ],
  "scenarios": [
    "EL-ETH-UTIL-DEON-01",
    "EL-CIV-FREE-HARM-01",
    "MAI-BIO-CRISPR-01",
    "MAI-ECO-INFL-01",
    "APO-PHY-HEAT-TEMP-01",
    "APO-BIO-GENE-DETERM-01"
  ],
  "parameters": {
    "max_turns": 5,
    "judge_model": "anthropic.claude-3-5-sonnet-20241022-v2:0"
  }
}
EOF

# Upload to S3
aws s3 cp /tmp/socratic-config.json s3://$BUCKET_NAME/artifacts/config.json

echo "✅ Config uploaded to s3://$BUCKET_NAME/artifacts/config.json"
echo ""
echo "You can edit the config:"
echo "  aws s3 cp s3://$BUCKET_NAME/artifacts/config.json /tmp/config.json"
echo "  # Edit /tmp/config.json"
echo "  aws s3 cp /tmp/config.json s3://$BUCKET_NAME/artifacts/config.json"
