# Judge Results Analysis

Automated analysis of judge evaluation results to identify scoring issues and patterns.

## Description

This skill analyzes judge evaluation data to help debug scoring problems:
1. Fetches recent judge results from S3
2. Parses and validates JSON structure
3. Checks score distributions and identifies anomalies
4. Reports on common errors (JSON parsing, missing fields, etc.)
5. Provides score statistics across dimensions

## When to Use

- After deploying judge changes to verify scoring works
- When seeing unexpected uniform scores (all same value)
- To debug JSON parsing errors
- To validate score discrimination (not all 90+)
- To verify dimension scores are being calculated correctly

## Usage

```bash
claude-flow run judge-inspect
```

## Optional Parameters

```bash
# Analyze specific number of recent results
claude-flow run judge-inspect --count 20

# Focus on specific model
claude-flow run judge-inspect --model "anthropic.claude-3-5-sonnet"

# Check for specific issues
claude-flow run judge-inspect --check "json-parsing"
```

## Implementation

```python
import boto3
import json
from collections import defaultdict, Counter
import statistics

# Configuration
PROFILE = "mvp"
REGION = "us-east-1"
BUCKET_NAME = "socratic-bench-data-984906149037"
COUNT = int(os.getenv("COUNT", "10"))
MODEL_FILTER = os.getenv("MODEL", None)

print("🔍 Analyzing judge results...\n")

# Initialize AWS clients
session = boto3.Session(profile_name=PROFILE)
s3 = session.client('s3', region_name=REGION)

# Step 1: List recent judge results
print(f"Step 1: Fetching {COUNT} most recent judge results...")

paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix='raw/runs/')

judge_files = []
for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            if 'judge_' in obj['Key'] and obj['Key'].endswith('.json'):
                judge_files.append({
                    'key': obj['Key'],
                    'modified': obj['LastModified']
                })

# Sort by most recent and take COUNT
judge_files.sort(key=lambda x: x['modified'], reverse=True)
judge_files = judge_files[:COUNT]

print(f"✅ Found {len(judge_files)} judge results\n")

# Step 2: Analyze results
print("Step 2: Analyzing judge outputs...")

errors = []
scores_by_dimension = defaultdict(list)
overall_scores = []
json_parse_errors = 0
missing_fields = 0
valid_results = 0

for file_info in judge_files:
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_info['key'])
        data = json.loads(response['Body'].read())

        # Check for errors
        if data.get('error'):
            errors.append({
                'file': file_info['key'],
                'error': data['error']
            })
            if 'JSON' in data['error'] or 'Unterminated' in data['error']:
                json_parse_errors += 1
            continue

        # Extract scores
        scores = data.get('scores', {})
        if not scores:
            missing_fields += 1
            continue

        # Record dimension scores
        for dim in ['open_ended', 'probing_depth', 'non_directive', 'age_appropriate', 'content_relevant']:
            if dim in scores:
                scores_by_dimension[dim].append(float(scores[dim]))

        # Record overall score
        if 'overall' in scores:
            overall_scores.append(float(scores['overall']))

        valid_results += 1

    except json.JSONDecodeError as e:
        json_parse_errors += 1
        errors.append({
            'file': file_info['key'],
            'error': f'JSON decode error: {str(e)}'
        })
    except Exception as e:
        errors.append({
            'file': file_info['key'],
            'error': str(e)
        })

print(f"✅ Analyzed {len(judge_files)} results\n")

# Step 3: Report findings
print("=" * 60)
print("JUDGE RESULTS ANALYSIS")
print("=" * 60)

print(f"\n📊 Summary:")
print(f"   Valid results: {valid_results}/{len(judge_files)}")
print(f"   JSON parsing errors: {json_parse_errors}")
print(f"   Missing fields: {missing_fields}")
print(f"   Other errors: {len(errors) - json_parse_errors}")

if valid_results > 0:
    print(f"\n📈 Score Statistics:")

    # Overall scores
    if overall_scores:
        print(f"\n   Overall Scores:")
        print(f"      Count: {len(overall_scores)}")
        print(f"      Mean: {statistics.mean(overall_scores):.1f}")
        print(f"      Median: {statistics.median(overall_scores):.1f}")
        print(f"      Min: {min(overall_scores):.1f}")
        print(f"      Max: {max(overall_scores):.1f}")
        print(f"      Std Dev: {statistics.stdev(overall_scores):.1f}" if len(overall_scores) > 1 else "      Std Dev: N/A")

        # Score distribution
        score_ranges = Counter()
        for score in overall_scores:
            if score < 50:
                score_ranges['0-49'] += 1
            elif score < 70:
                score_ranges['50-69'] += 1
            elif score < 85:
                score_ranges['70-84'] += 1
            else:
                score_ranges['85-100'] += 1

        print(f"\n   Distribution:")
        for range_name in ['0-49', '50-69', '70-84', '85-100']:
            count = score_ranges[range_name]
            pct = (count / len(overall_scores)) * 100
            bar = '█' * int(pct / 5)
            print(f"      {range_name}: {count:2d} ({pct:5.1f}%) {bar}")

    # Dimension scores
    print(f"\n   Dimension Scores:")
    for dim in ['open_ended', 'probing_depth', 'non_directive', 'age_appropriate', 'content_relevant']:
        if dim in scores_by_dimension:
            dim_scores = scores_by_dimension[dim]
            print(f"      {dim:20s}: mean={statistics.mean(dim_scores):5.1f}, "
                  f"range=[{min(dim_scores):5.1f}, {max(dim_scores):5.1f}], "
                  f"n={len(dim_scores)}")

    # Check for suspicious patterns
    print(f"\n⚠️  Potential Issues:")
    issues_found = False

    # All scores identical
    if overall_scores and len(set(overall_scores)) == 1:
        print(f"   🔴 All overall scores are identical: {overall_scores[0]}")
        issues_found = True

    # All scores too high
    if overall_scores and statistics.mean(overall_scores) > 85:
        print(f"   🟡 Mean score suspiciously high: {statistics.mean(overall_scores):.1f} (should use full 0-100 range)")
        issues_found = True

    # No variation in dimension scores
    for dim, dim_scores in scores_by_dimension.items():
        if len(set(dim_scores)) == 1:
            print(f"   🔴 All {dim} scores identical: {dim_scores[0]}")
            issues_found = True

    if not issues_found:
        print(f"   ✅ No obvious issues detected")

if errors:
    print(f"\n❌ Errors ({len(errors)}):")
    for error in errors[:5]:  # Show first 5
        print(f"   - {error['file'].split('/')[-1]}: {error['error'][:100]}")
    if len(errors) > 5:
        print(f"   ... and {len(errors) - 5} more errors")

print()
```

## Output

```
🔍 Analyzing judge results...

Step 1: Fetching 10 most recent judge results...
✅ Found 10 judge results

Step 2: Analyzing judge outputs...
✅ Analyzed 10 results

============================================================
JUDGE RESULTS ANALYSIS
============================================================

📊 Summary:
   Valid results: 10/10
   JSON parsing errors: 0
   Missing fields: 0
   Other errors: 0

📈 Score Statistics:

   Overall Scores:
      Count: 10
      Mean: 78.3
      Median: 79.5
      Min: 68.0
      Max: 90.0
      Std Dev: 7.2

   Distribution:
      0-49:  0 ( 0.0%)
      50-69:  2 (20.0%) ████
      70-84:  6 (60.0%) ████████████
      85-100:  2 (20.0%) ████

   Dimension Scores:
      open_ended         : mean= 75.6, range=[ 60.0,  85.0], n=10
      probing_depth      : mean= 72.8, range=[ 55.0,  88.0], n=10
      non_directive      : mean= 80.2, range=[ 70.0,  90.0], n=10
      age_appropriate    : mean= 85.1, range=[ 78.0,  92.0], n=10
      content_relevant   : mean= 87.8, range=[ 82.0,  95.0], n=10

⚠️  Potential Issues:
   ✅ No obvious issues detected
```

## Notes

- Analyzes most recent judge results by default
- Detects common issues: JSON parsing, missing fields, identical scores
- Shows score distribution to verify judge is discriminating
- Use after deploying judge changes to verify correctness
- Requires `boto3` Python package
