# Claude Skills for Socratic AI Benchmarks

This directory contains reusable skills for common development tasks on the Socratic AI Benchmarking Platform. Use these as references for recurring work patterns.

## Available Skills

### 1. **UI Deploy Pipeline** (`ui-deploy-pipeline.md`)
One-command deployment for UI changes (HTML/CSS/JS) to CloudFront.

**When to use**: After editing `serverless/ui/` files
**Key tasks**: Deploy to S3, invalidate CloudFront, verify changes live
**Output**: Updated UI at https://d3ic7ds776p9cq.cloudfront.net/

### 2. **Chart Debugging** (`chart-debugging.md`)
Diagnose and fix Chart.js rendering issues, data scaling problems, visualization bugs.

**When to use**: Charts show wrong data, missing models, incorrect scaling
**Key tasks**: Identify scaling mismatch, verify API response format, fix chart configuration
**Common fix**: Remove duplicate score multiplications (API returns 0-10, don't multiply by 100)

### 3. **API Debugging** (`api-debugging.md`)
Diagnose and fix Lambda API endpoints, data transformations, DynamoDB queries.

**When to use**: Endpoints return wrong data, 500 errors, empty results
**Key tasks**: Test endpoints, check Lambda logs, verify score scaling, fix DynamoDB queries
**Related**: All 5 API routes documented with examples

### 4. **Git Commit and Deploy** (`git-commit-deploy.md`)
Standard workflow for committing code, deploying to AWS, pushing to GitHub.

**When to use**: After every code change (MANDATORY per CLAUDE.md)
**Key tasks**: Stage changes, commit with good message, deploy with CDK, push to main
**Message format**: `<type>: <description>` (fix, feat, style, docs, refactor, etc.)

### 5. **Model Configuration and Testing** (`model-config-and-test.md`)
Add new models, configure parameters, run invocations, verify integration.

**When to use**: Adding new model (e.g., Gemini), testing new provider
**Key tasks**: Update config, create client module, add routing, set env vars, test
**Example**: Gemini 3 Pro Preview integration steps

### 6. **Documentation and Methodology** (`docs-and-methodology.md`)
Update documentation, methodology pages, homepage content.

**When to use**: Framework changes, docs out of sync, new documentation needed
**Key tasks**: Update HTML files, verify consistency, check CSS/fonts, deploy
**Checklist**: Framework definitions, scenarios, scoring table, examples

## Quick Reference: Rote Actions Mapped to Skills

| Rote Action | Skill | Command |
|-------------|-------|---------|
| Fix chart displaying wrong data | Chart Debugging | Use diagnostics in chart-debugging.md |
| Add new AI model | Model Config | Follow steps in model-config-and-test.md |
| Deploy UI changes | UI Deploy Pipeline | `cdk deploy --profile mvp` |
| Fix API endpoint issue | API Debugging | Use endpoint test commands |
| Update homepage | Documentation | Edit index.html, then deploy |
| Update methodology page | Documentation | Edit methodology.html, then deploy |
| Commit and push changes | Git Commit | `git add -A && git commit -m "..."` |
| Verify chart scales correctly | Chart Debugging | Check score conversion 0-1 → 0-10 |
| Test Lambda function | API Debugging | Use `aws lambda invoke` command |
| Check CloudWatch logs | API Debugging | Use `aws logs tail` command |

## Score Scaling Rules (Critical)

This is referenced by multiple skills. Remember:

```
Judge Output (LLM)  → 0-1 scale (e.g., 0.91)
DynamoDB Storage    → 0-1 scale (e.g., 0.91)
API Response        → 0-10 scale (multiply by 10) (e.g., 9.1)
Chart.js Render     → 0-10 scale (use directly)
UI Bar Width        → % (multiply by 10)
```

**Common mistake**: Multiplying by 100 in charts when API already returns 0-10.

## AWS Profile Requirement

All AWS commands MUST use `--profile mvp`. This is non-negotiable per CLAUDE.md.

```bash
# WRONG
aws dynamodb scan --table-name socratic_core

# CORRECT
aws dynamodb scan --table-name socratic_core --profile mvp
```

## Project Paths

| Component | Path |
|-----------|------|
| UI Files | `serverless/ui/` (HTML, CSS, JS) |
| API Handler | `serverless/lambdas/api/handler.py` |
| Models | `serverless/lib/socratic_bench/` |
| Config | `serverless/config-24-models.json` |
| Infrastructure | `serverless/infra/` (CDK code) |
| Environment | Set `GOOGLE_API_KEY` for Gemini integration |

## Key API Endpoints

All endpoints return proper 0-10 scale scores:

```
GET /api/model-comparison       - Top models by metric
GET /api/timeseries            - Score trends over 52 weeks
GET /api/latest-rankings       - Current week rankings
GET /api/detailed-results      - Individual test results
GET /api/cost-analysis         - Cost vs performance scatter
```

## Common Patterns

### Pattern 1: Fix Chart Display
1. Open DevTools (F12)
2. Check Network tab for API response
3. Check Console for JS errors
4. Compare data values with chart scale
5. Fix multiplication factor if needed

### Pattern 2: Deploy Changes
1. `git add -A`
2. `git commit -m "..."`
3. `cdk deploy --profile mvp --require-approval never`
4. `git push origin main`
5. Test at https://d3ic7ds776p9cq.cloudfront.net/

### Pattern 3: Add New Model
1. Edit `config-24-models.json`
2. Add provider routing in `models.py` (if new provider)
3. Set environment variable (if needed)
4. Run one-time test
5. Deploy
6. Verify in dashboard

## Documentation Sources

| Document | Purpose | Last Updated |
|----------|---------|--------------|
| `socratic.md` | Framework definition | Nov 2025 |
| `ARCHITECTURE.md` | System design | Nov 2025 |
| `CLAUDE.md` | Development guidelines | Nov 2025 |
| This file | Skill index | Nov 2025 |

## Getting Started

Pick the skill matching your task:

1. **Making UI changes?** → `ui-deploy-pipeline.md`
2. **Charts broken?** → `chart-debugging.md`
3. **API not working?** → `api-debugging.md`
4. **Done with code?** → `git-commit-deploy.md`
5. **Adding a model?** → `model-config-and-test.md`
6. **Updating docs?** → `docs-and-methodology.md`

Then follow the workflow steps in the chosen skill.

## Related Resources

- Main project: `/Users/williamprior/Development/GitHub/socratic-ai-benchmarks`
- Configuration: `/Users/williamprior/CLAUDE.md`
- Live dashboard: https://d3ic7ds776p9cq.cloudfront.net/
- GitHub: https://github.com/socratic-ai-institute/socratic-ai-benchmarks
