#!/bin/bash
# Check SQS queue depths

set -e

echo "📊 Checking SQS queue depths..."
echo ""

# Dialogue queue
DIALOGUE_URL=$(aws sqs get-queue-url --queue-name socratic-dialogue-jobs --query 'QueueUrl' --output text)
DIALOGUE_COUNT=$(aws sqs get-queue-attributes \
  --queue-url $DIALOGUE_URL \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' \
  --output text)

echo "Dialogue jobs queue: $DIALOGUE_COUNT messages"

# Judge queue
JUDGE_URL=$(aws sqs get-queue-url --queue-name socratic-judge-jobs --query 'QueueUrl' --output text)
JUDGE_COUNT=$(aws sqs get-queue-attributes \
  --queue-url $JUDGE_URL \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' \
  --output text)

echo "Judge jobs queue: $JUDGE_COUNT messages"

# DLQs
DIALOGUE_DLQ_URL=$(aws sqs get-queue-url --queue-name socratic-dialogue-dlq --query 'QueueUrl' --output text)
DIALOGUE_DLQ_COUNT=$(aws sqs get-queue-attributes \
  --queue-url $DIALOGUE_DLQ_URL \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' \
  --output text)

echo "Dialogue DLQ: $DIALOGUE_DLQ_COUNT messages"

JUDGE_DLQ_URL=$(aws sqs get-queue-url --queue-name socratic-judge-dlq --query 'QueueUrl' --output text)
JUDGE_DLQ_COUNT=$(aws sqs get-queue-attributes \
  --queue-url $JUDGE_DLQ_URL \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' \
  --output text)

echo "Judge DLQ: $JUDGE_DLQ_COUNT messages"

if [ "$DIALOGUE_DLQ_COUNT" != "0" ] || [ "$JUDGE_DLQ_COUNT" != "0" ]; then
    echo ""
    echo "⚠️  Warning: Messages found in DLQ! Check for errors."
fi
