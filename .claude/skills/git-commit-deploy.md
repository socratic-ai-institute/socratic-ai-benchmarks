# Git Commit and Deploy Skill

## Description
Standard workflow for committing code changes, deploying to AWS, and pushing to GitHub.

## When to Use
- After completing any code fix or feature
- Before moving to next task
- When combining multiple small changes into one deployment
- Required by project CLAUDE.md (MANDATORY workflow)

## Full Workflow

### 1. Stage Changes
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks

# Review what changed
git status

# View diffs before committing
git diff
```

### 2. Add All Changes
```bash
git add -A
```

### 3. Commit with Descriptive Message
Message format: `<type>: <description>`

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code restructuring (no behavior change)
- `style:` - Font, colors, styling (no logic change)
- `docs:` - Documentation updates
- `test:` - Test additions/changes
- `chore:` - Build, deps, config

Examples:
```bash
# Chart scaling fix
git commit -m "fix: Remove duplicate score scaling in chart rendering (API already converts to 0-10)"

# UI styling
git commit -m "style: Change site font to IBM Plex Mono and nav links to white"

# Gemini integration
git commit -m "feat: Add Google Gemini 3 Pro Preview integration with google-genai SDK"

# Data mapping
git commit -m "fix: Map scenario IDs to user-friendly names in API endpoint"
```

### 4. Deploy to AWS
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks/serverless/infra

# Set Google API key if needed (usually already set in environment)
export GOOGLE_API_KEY="AIzaSyCqHKQ9VQ-gXJgkSqyq6Rx3pZP0sVNYv5c"

# Deploy with --profile mvp (MANDATORY)
cdk deploy --profile mvp --require-approval never
```

### 5. Verify Deployment
```bash
# Wait for CloudFormation to complete
# Check output for "✨  Deployment successful"

# Verify stack updated
aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile mvp \
  --query 'Stacks[0].StackStatus'
```

### 6. Push to GitHub
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks

# Push to main branch
git push origin main

# Verify push succeeded
git log --oneline -3
```

### 7. Verify Live Deployment
```bash
# Check CloudFront distribution
aws cloudfront list-distributions --profile mvp | grep -A2 "d3ic7ds776p9cq"

# Test API endpoints
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/latest-rankings | jq '.rankings | length'

# Visit live site
# https://d3ic7ds776p9cq.cloudfront.net/
```

## Success Criteria
- Git shows "created/changed" count
- CDK deploy completes without errors
- Git push succeeds
- All GitHub checks pass
- Live site reflects changes

## Common Issues

### CDK Deploy Fails
```bash
# Check AWS credentials
aws sts get-caller-identity --profile mvp

# Verify profile exists
aws configure list --profile mvp

# Check CloudFormation for errors
aws cloudformation describe-stack-events \
  --stack-name SocraticBenchStack \
  --profile mvp | jq '.StackEvents[0:5]'
```

### Git Push Fails
```bash
# Fetch latest
git fetch origin

# Rebase if behind
git rebase origin/main

# Try push again
git push origin main

# Force push only if absolutely necessary
git push -f origin main  # Use with caution!
```

### Nothing Changed
```bash
# Verify files were actually edited
git status --porcelain

# If empty, nothing changed
# No need to commit

# If files listed, proceed with staging
```

## Commit Message Best Practices

✅ GOOD:
```
fix: Correct score scaling in timeseries chart (remove duplicate * 100)
feat: Add Gemini 3 Pro model to benchmarking suite
style: Update nav link colors to white for better contrast
```

❌ BAD:
```
fixed stuff
updated code
changed things
final fix (really this time)
```

## Required by CLAUDE.md

This workflow is **MANDATORY** per `/Users/williamprior/Development/GitHub/socratic-ai-benchmarks/CLAUDE.md`:

> After completing ANY task or making ANY changes, you MUST:
> 1. Run Tests First (if applicable)
> 2. Stage All Changes: `git add .`
> 3. Commit with Descriptive Message
> 4. Push to Main: `git push origin main`

## Related Commands
- `git log --oneline -10` - See recent commits
- `git diff HEAD~1` - See last commit changes
- `git reset --soft HEAD~1` - Undo last commit (keep changes)
- `git revert HEAD` - Create new commit undoing last one
