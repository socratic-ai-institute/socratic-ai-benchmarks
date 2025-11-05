#!/bin/bash
# Trigger a manual test run

set -e

echo "🧪 Triggering manual test run..."

# Invoke Planner Lambda
FUNCTION_NAME="SocraticBenchStack-PlannerFunction"

echo "Invoking $FUNCTION_NAME..."
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --payload '{"source": "manual-test"}' \
  /tmp/planner-response.json

echo ""
echo "📄 Planner Response:"
cat /tmp/planner-response.json | jq .

echo ""
echo "✅ Test run initiated!"
echo ""
echo "Check progress:"
echo "  aws logs tail /aws/lambda/SocraticBenchStack-PlannerFunction --follow"
echo "  aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction --follow"
echo "  aws logs tail /aws/lambda/SocraticBenchStack-JudgeFunction --follow"
echo ""
echo "Check queue depth:"
echo "  ./scripts/check-queues.sh"
