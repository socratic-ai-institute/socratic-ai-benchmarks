# Lambda Logs Streaming

Real-time streaming and analysis of AWS Lambda function logs for debugging.

## Description

This skill streams and analyzes Lambda function logs:
1. Lists available Lambda functions in the stack
2. Streams CloudWatch logs in real-time
3. Filters for errors, warnings, or custom patterns
4. Highlights important log entries
5. Provides log statistics and error summaries

## When to Use

- Debugging Lambda function errors
- Monitoring judge, runner, or planner execution
- Investigating JSON parsing or scoring issues
- Tracking API request/response flow
- Analyzing performance and latency

## Usage

```bash
# Stream logs from API Lambda
claude-flow run lambda-logs --function ApiFunction

# Stream judge Lambda logs
claude-flow run lambda-logs --function JudgeFunction

# Filter for errors only
claude-flow run lambda-logs --function ApiFunction --filter ERROR

# Stream with custom time range
claude-flow run lambda-logs --function ApiFunction --minutes 30
```

## Optional Parameters

- `--function`: Lambda function name (ApiFunction, JudgeFunction, RunnerFunction, PlannerFunction, CuratorFunction)
- `--filter`: Filter pattern (ERROR, WARNING, JSON, or custom regex)
- `--minutes`: Look back N minutes (default: 10)
- `--follow`: Keep streaming new logs (default: false)

## Implementation

```python
import boto3
import time
from datetime import datetime, timedelta
import re
import os

# Configuration
PROFILE = "mvp"
REGION = "us-east-1"
FUNCTION_NAME = os.getenv("FUNCTION", "ApiFunction")
FILTER_PATTERN = os.getenv("FILTER", None)
MINUTES = int(os.getenv("MINUTES", "10"))
FOLLOW = os.getenv("FOLLOW", "false").lower() == "true"

# Map short names to full Lambda function names
FUNCTION_MAP = {
    "ApiFunction": "SocraticBenchStack-ApiFunction",
    "JudgeFunction": "SocraticBenchStack-JudgeFunction",
    "RunnerFunction": "SocraticBenchStack-RunnerFunction",
    "PlannerFunction": "SocraticBenchStack-PlannerFunction",
    "CuratorFunction": "SocraticBenchStack-CuratorFunction",
}

full_function_name = FUNCTION_MAP.get(FUNCTION_NAME, FUNCTION_NAME)

print(f"📋 Streaming logs for {full_function_name}...\n")

# Initialize AWS clients
session = boto3.Session(profile_name=PROFILE)
logs_client = session.client('logs', region_name=REGION)

# Get log group name
log_group = f"/aws/lambda/{full_function_name}"

# Calculate time range
end_time = datetime.utcnow()
start_time = end_time - timedelta(minutes=MINUTES)

start_ms = int(start_time.timestamp() * 1000)
end_ms = int(end_time.timestamp() * 1000)

print(f"Time range: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')} UTC")
if FILTER_PATTERN:
    print(f"Filter: {FILTER_PATTERN}")
print()

# Counters
error_count = 0
warning_count = 0
total_lines = 0

# Color codes for terminal
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
RESET = '\033[0m'

def colorize_log(message):
    """Add color to log lines based on content."""
    if 'ERROR' in message or 'Exception' in message or 'Traceback' in message:
        return f"{RED}{message}{RESET}"
    elif 'WARNING' in message or 'WARN' in message:
        return f"{YELLOW}{message}{RESET}"
    elif 'SUCCESS' in message or 'completed' in message:
        return f"{GREEN}{message}{RESET}"
    elif 'INFO' in message or 'Processing' in message:
        return f"{BLUE}{message}{RESET}"
    return message

try:
    # Stream logs
    kwargs = {
        'logGroupName': log_group,
        'startTime': start_ms,
        'interleaved': True,
    }

    if FILTER_PATTERN:
        kwargs['filterPattern'] = FILTER_PATTERN

    while True:
        response = logs_client.filter_log_events(**kwargs)

        for event in response.get('events', []):
            message = event['message'].rstrip()
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')

            # Count errors/warnings
            if 'ERROR' in message or 'Exception' in message:
                error_count += 1
            elif 'WARNING' in message or 'WARN' in message:
                warning_count += 1

            total_lines += 1

            # Print with color
            print(f"[{timestamp}] {colorize_log(message)}")

        if not FOLLOW:
            break

        if 'nextToken' in response:
            kwargs['nextToken'] = response['nextToken']
        else:
            if FOLLOW:
                # Wait and continue polling
                time.sleep(2)
                kwargs['startTime'] = end_ms
                end_ms = int(datetime.utcnow().timestamp() * 1000)
            else:
                break

except logs_client.exceptions.ResourceNotFoundException:
    print(f"{RED}❌ Log group not found: {log_group}{RESET}")
    print(f"\nAvailable functions:")
    for name in FUNCTION_MAP.keys():
        print(f"   - {name}")
    exit(1)

except KeyboardInterrupt:
    print(f"\n\n{YELLOW}Streaming interrupted{RESET}")

# Print summary
print(f"\n{'=' * 60}")
print(f"LOG SUMMARY")
print(f"{'=' * 60}")
print(f"Total lines: {total_lines}")
print(f"Errors: {RED}{error_count}{RESET}")
print(f"Warnings: {YELLOW}{warning_count}{RESET}")
print()
```

## Output

```
📋 Streaming logs for SocraticBenchStack-ApiFunction...

Time range: 10:45:23 - 10:55:23 UTC

[10:47:15] START RequestId: a8f3c9d2-1234-5678-90ab-cdef12345678 Version: $LATEST
[10:47:15] Processing GET /api/model-comparison
[10:47:15] Fetching latest run for each model...
[10:47:16] Found 12 models with completed runs
[10:47:16] Fetching judge results from S3...
[10:47:17] SUCCESS: Returned model comparison data
[10:47:17] END RequestId: a8f3c9d2-1234-5678-90ab-cdef12345678
[10:47:17] REPORT RequestId: a8f3c9d2-1234-5678-90ab-cdef12345678  Duration: 1853.26 ms  Billed Duration: 1854 ms  Memory Size: 512 MB  Max Memory Used: 128 MB

[10:48:32] START RequestId: b7e4d8c1-2345-6789-01bc-def123456789 Version: $LATEST
[10:48:32] Processing POST /trigger-planner
[10:48:32] ERROR: Failed to parse request body: Expecting value: line 1 column 1 (char 0)
[10:48:32] Traceback (most recent call last):
[10:48:32]   File "/var/task/handler.py", line 143, in trigger_planner
[10:48:32]     body = json.loads(event.get('body', '{}'))
[10:48:32] json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
[10:48:32] END RequestId: b7e4d8c1-2345-6789-01bc-def123456789
[10:48:32] REPORT RequestId: b7e4d8c1-2345-6789-01bc-def123456789  Duration: 45.12 ms  Billed Duration: 46 ms  Memory Size: 512 MB  Max Memory Used: 85 MB

============================================================
LOG SUMMARY
============================================================
Total lines: 24
Errors: 3
Warnings: 0
```

## Notes

- Uses AWS profile 'mvp' - ensure credentials are configured
- Logs are color-coded: Red (errors), Yellow (warnings), Green (success), Blue (info)
- Use `--follow` to keep streaming new logs (Ctrl+C to stop)
- Default looks back 10 minutes
- Common filters: ERROR, WARNING, JSON, Exception
- Requires `boto3` Python package
