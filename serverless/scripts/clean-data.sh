#!/bin/bash
# Clean all data from DynamoDB and S3 for fresh test runs
# WARNING: This will delete ALL benchmark data!

set -e

PROFILE="mvp"
REGION="us-east-1"
TABLE_NAME="socratic_core"
BUCKET_NAME="socratic-bench-data-984906149037"

echo "🧹 Cleaning Socratic Benchmark Data..."
echo ""
echo "⚠️  WARNING: This will delete ALL data from:"
echo "   - DynamoDB table: $TABLE_NAME"
echo "   - S3 bucket: $BUCKET_NAME"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

echo ""
echo "📋 Step 1: Cleaning DynamoDB table: $TABLE_NAME"
echo "----------------------------------------"

# Get all items from DynamoDB table
echo "Scanning table for items to delete..."
ITEMS=$(aws dynamodb scan \
    --table-name "$TABLE_NAME" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --output json)

# Count items
ITEM_COUNT=$(echo "$ITEMS" | jq '.Items | length')
echo "Found $ITEM_COUNT items"

if [ "$ITEM_COUNT" -gt 0 ]; then
    echo "Deleting items..."

    # Delete each item
    echo "$ITEMS" | jq -c '.Items[]' | while read -r item; do
        PK=$(echo "$item" | jq -r '.PK.S')
        SK=$(echo "$item" | jq -r '.SK.S')

        aws dynamodb delete-item \
            --table-name "$TABLE_NAME" \
            --key "{\"PK\": {\"S\": \"$PK\"}, \"SK\": {\"S\": \"$SK\"}}" \
            --profile "$PROFILE" \
            --region "$REGION" \
            --no-cli-pager > /dev/null

        echo "  ✓ Deleted: PK=$PK, SK=$SK"
    done

    echo "✅ DynamoDB table cleaned ($ITEM_COUNT items deleted)"
else
    echo "✅ DynamoDB table already empty"
fi

echo ""
echo "📦 Step 2: Cleaning S3 bucket: $BUCKET_NAME"
echo "----------------------------------------"

# Count objects in bucket
OBJECT_COUNT=$(aws s3 ls s3://$BUCKET_NAME --recursive --profile "$PROFILE" | wc -l)
echo "Found $OBJECT_COUNT objects"

if [ "$OBJECT_COUNT" -gt 0 ]; then
    echo "Deleting all objects from bucket..."

    # Delete all objects in raw/ prefix
    aws s3 rm s3://$BUCKET_NAME/raw/ --recursive --profile "$PROFILE" --region "$REGION"
    echo "  ✓ Deleted raw/ prefix"

    # Delete all objects in curated/ prefix
    aws s3 rm s3://$BUCKET_NAME/curated/ --recursive --profile "$PROFILE" --region "$REGION"
    echo "  ✓ Deleted curated/ prefix"

    # Delete all objects in manifests/ prefix (but keep artifacts/)
    aws s3 rm s3://$BUCKET_NAME/manifests/ --recursive --profile "$PROFILE" --region "$REGION"
    echo "  ✓ Deleted manifests/ prefix"

    echo "✅ S3 bucket cleaned"
else
    echo "✅ S3 bucket already empty"
fi

echo ""
echo "🎉 Data cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Run: ./serverless/scripts/test-run.sh"
echo "  2. Or trigger via EventBridge schedule"
echo ""
