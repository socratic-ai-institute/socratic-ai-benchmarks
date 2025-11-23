# UI Deploy Pipeline Skill

## Description
One-command deployment for UI changes to CloudFront with CDK, testing, and git operations.

## When to Use
- After making changes to HTML/CSS/JS in `serverless/ui/`
- When updating front-end styling or layouts
- After fixing chart rendering or component issues

## Quick Start
```bash
./claude-flow sparc "Deploy UI changes" --skill ui-deploy-pipeline
```

## Full Workflow

### 1. Validate Changes
```bash
# Check what files were modified
git status

# Preview changes (if text files)
git diff serverless/ui/
```

### 2. Deploy to AWS
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks/serverless/infra
cdk deploy --profile mvp --require-approval never
```

### 3. Commit and Push
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks
git add -A
git commit -m "ui: [describe changes]"
git push origin main
```

### 4. Verify CloudFront Cache
After deployment, CloudFront invalidation is automatic via CDK. Verify by:
```bash
# Check distribution status
aws cloudfront list-distributions --profile mvp | grep -A2 "d3ic7ds776p9cq"

# Force refresh in browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

## Success Criteria
- CDK deploy completes without errors
- Files appear in S3 bucket: `socratic-bench-ui-{account}`
- CloudFront invalidation created
- Changes visible at https://d3ic7ds776p9cq.cloudfront.net/

## Common Issues

### CDK Deploy Fails
- Verify AWS profile: `aws sts get-caller-identity --profile mvp`
- Check CDK version: `cdk --version`
- Check for uncommitted changes in infra code

### Changes Not Visible
- Clear browser cache: Hard refresh (Cmd+Shift+R)
- Check CloudFront invalidation status
- Verify files uploaded to S3: `aws s3 ls s3://socratic-bench-ui-{account}/ --profile mvp`

### Git Push Fails
- Ensure main branch is up to date: `git fetch origin && git rebase origin/main`
- Check for merge conflicts
- Verify GitHub token is valid

## Related Commands
- `aws s3 ls s3://socratic-bench-ui-984906149037/ --profile mvp` - List UI files
- `aws cloudfront list-invalidations --profile mvp --distribution-id E27XYZABC` - Check invalidations
