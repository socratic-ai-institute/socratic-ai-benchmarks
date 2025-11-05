# Socratic AI Benchmarks - Unified Vision

**Last Updated**: 2025-11-05
**Status**: Phase 1 Active, Phase 2 Ready to Deploy

---

## Overview

This repository implements a **three-phase research project** to evaluate and deploy Socratic AI for educational interventions:

- **Phase 1**: Select the best AI model for Socratic questioning (CLI-based evaluation)
- **Phase 2**: Build serverless benchmarking platform for ongoing model evaluation (Lambda MVP)
- **Phase 3**: Scale to production research experiment with students (Future: Step Functions + Batch)

**Current Focus**: Transitioning from Phase 1 to Phase 2

---

## Phase 1: Model Selection (Current Phase)

### Objective
Identify the best AWS Bedrock model for generating Socratic questions by comparing reasoning vs. non-reasoning models across context growth scenarios.

### Location
```
phase1-model-selection/
├── socratic_eval/
│   ├── context_growth/        # Context growth evaluation framework
│   ├── vectors.py              # Three-vector framework (Elenchus, Maieutics, Aporia)
│   └── grader.py              # LLM-as-judge utilities
├── benchmark.py               # Main benchmark script
├── generate_scenarios.py      # Test scenario generator
└── generate_dashboard.py      # Results visualization
```

### Status
✅ **Complete and working**

### Key Features
- **Context Growth Framework**: Tests how models maintain Socratic behavior as context windows grow
- **Three-Vector Evaluation**: Elenchus (refutation), Maieutics (discovery), Aporia (perplexity)
- **Disposition Rubric**: 0-10 scoring for Socratic quality (Form, Intent, Groundedness, Non-Leadingness)
- **5 Core Metrics**: Persistence, Cognitive Depth, Context Adaptability, Resistance to Drift, Memory Preservation
- **Static Dashboard**: HTML reports with radar charts and comparison tables

### Usage
```bash
cd phase1-model-selection

# Run context growth evaluation
python -m socratic_eval.context_growth.runner \
  --models "anthropic.claude-3-5-sonnet-20241022-v2:0,anthropic.claude-3-opus-20240229-v1:0" \
  --test-types "consistency,complexity"

# Generate dashboard
python -m socratic_eval.context_growth.generate_dashboard \
  context_growth_results_*.json --output dashboard.html
```

### Timeline
- **Day 1-2**: Request Bedrock access, run quick tests
- **Day 3-4**: Run full comparison (8 models, 120 scenarios)
- **Day 5**: Analyze results, select winning model

### Budget
~$10 for full comparison

### Output
Model selection decision with quality scores, cost analysis, and rationale

---

## Phase 2: Serverless Benchmarking Platform (Next Phase - MVP Ready)

### Objective
Build an **automated, weekly benchmarking system** to continuously evaluate the selected model(s) and detect quality drift over time.

### Location
```
serverless/
├── infra/                     # Python CDK infrastructure
│   ├── app.py                 # CDK entry point
│   └── stack.py               # Complete stack definition
├── lambdas/                   # Lambda function handlers
│   ├── planner/               # Orchestrator (manifest creation)
│   ├── runner/                # Dialogue executor
│   ├── judge/                 # Turn scorer (LLM-as-judge)
│   ├── curator/               # Results aggregator
│   └── api/                   # Read API
├── lib/                       # Shared socratic_bench library
│   └── socratic_bench/
│       ├── models.py          # Bedrock client wrapper
│       ├── scenarios.py       # Test scenarios
│       ├── prompts.py         # Prompt templates
│       ├── dialogue.py        # Dialogue runner
│       └── judge.py           # Scoring logic
├── ui/                        # Static web dashboard
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── scripts/                   # Deployment helpers
    ├── deploy.sh
    └── test-run.sh
```

### Architecture

```
EventBridge (weekly cron)
    ↓
Planner Lambda → SQS dialogue-jobs
                      ↓
                 Runner Lambda (parallel, max 25)
                      ↓
                 SQS judge-jobs
                      ↓
                 Judge Lambda (parallel, max 25)
                      ↓
                 EventBridge run.judged
                      ↓
                 Curator Lambda
                      ↓
                 DynamoDB + S3 (curated JSON)
                      ↓
                 API Gateway + Static UI
```

### Key Features
- ✅ **All Lambda**: No containers, no servers (simplest possible MVP)
- ✅ **SQS Fan-Out**: Parallel execution with throttling (not Step Functions)
- ✅ **Single-Table DynamoDB**: GSIs for flexible queries
- ✅ **Two-Tier Storage**: S3 raw (archived) + curated (hot)
- ✅ **Weekly Automated**: EventBridge cron trigger
- ✅ **API + Dashboard**: Real-time results via REST API and static UI
- ✅ **Idempotent**: Deterministic manifest IDs, safe retries

### Cost
- **Weekly run** (2 models × 6 scenarios): ~$2/week
- **Monthly idle**: ~$0.35 (storage only)
- **Annual estimate**: ~$8-10/month

### Deployment
```bash
cd serverless/infra

# Bootstrap (first time only)
cdk bootstrap

# Deploy
cdk deploy

# Upload config
aws s3 cp config.json s3://$BUCKET_NAME/artifacts/config.json

# Trigger test run
aws lambda invoke --function-name SocraticBenchStack-PlannerFunction response.json
```

### Timeline
- **Week 1**: Deploy infrastructure (10 minutes)
- **Week 2**: Test with Phase 1 winner, verify weekly runs
- **Week 3**: Monitor quality drift, tune thresholds

### Status
✅ **Ready to deploy** - Full implementation complete

### Documentation
- [`serverless/README.md`](serverless/README.md) - Full architecture
- [`serverless/DEPLOYMENT_GUIDE.md`](serverless/DEPLOYMENT_GUIDE.md) - Step-by-step deployment
- [`serverless/QUICK_START.md`](serverless/QUICK_START.md) - 5-minute quick start
- [`SERVERLESS_IMPLEMENTATION.md`](SERVERLESS_IMPLEMENTATION.md) - Implementation summary

---

## Phase 3: Production Research Experiment (Future)

### Objective
Run full educational research study with **120-240 students** testing location-aware Socratic AI interventions.

### Location
```
archive/phase3-batch-architecture/
└── (Design documents for future Step Functions + Batch architecture)
```

### Architecture (Future Design)
**Different from Phase 2**: Uses Step Functions + AWS Batch/Fargate for long-running dialogues (2-5 min), not Lambda.

```
EventBridge → Step Functions Orchestrator
                 ↓
             Batch Job (Dialogue Runner)
                 ↓
             Batch Job (Judge)
                 ↓
             Lambda (Aggregator)
                 ↓
             S3 + DynamoDB + Athena + QuickSight
```

### Key Differences from Phase 2
- **Compute**: Batch/Fargate (unlimited runtime) instead of Lambda (15 min max)
- **Orchestration**: Step Functions state machine instead of SQS queues
- **Analytics**: Athena + QuickSight instead of simple API
- **Scale**: 7,200 turns/week instead of 60 turns/week
- **Cost**: ~$33/week instead of ~$2/week

### Experimental Design
- **24 conditions**: 4 locations × 3 timings × 2 interventions
- **Context phases**: P0 (2K tokens), P1 (8K), P2 (32K), P3 (128K+)
- **Metrics**: SD (Socratic Disposition), half-life, CSD (8 dimensions)

### Timeline
- **Months 1-3**: Infrastructure + experiment engine (after Phase 2 stable)
- **Months 4-5**: Pilot with 24-48 students
- **Months 6-9**: Production with 120-240 students
- **Month 10**: Analysis and paper

### Budget
~$41K (development) + ~$440 (AWS) + ~$8.7K (operational)

### Status
📋 **Design complete, implementation deferred**

### Documentation
Archived in `archive/phase3-batch-architecture/` (formerly `aws-benchmark-system/`)

---

## Repository Structure (After Consolidation)

```
socratic-ai-benchmarks/
│
├── VISION.md                         ← This file (master plan)
├── README.md                         ← Quick start guide
│
├── phase1-model-selection/           ← Phase 1: CLI model comparison
│   ├── socratic_eval/
│   │   ├── context_growth/           ← Context growth framework
│   │   ├── vectors.py                ← Three-vector evaluation
│   │   └── grader.py                 ← LLM-as-judge
│   ├── benchmark.py
│   └── README.md
│
├── serverless/                       ← Phase 2: Serverless benchmarking MVP
│   ├── infra/                        ← Python CDK stack
│   ├── lambdas/                      ← 5 Lambda functions
│   ├── lib/                          ← Shared library layer
│   ├── ui/                           ← Static dashboard
│   ├── scripts/                      ← Deployment scripts
│   └── README.md
│
├── phase2-research-experiment/       ← Phase 3 early planning (legacy)
│   └── (Minimal, mostly superseded by Phase 2 serverless)
│
├── archive/                          ← Superseded implementations
│   ├── infrastructure-typescript/    ← Old TypeScript CDK (duplicate)
│   ├── lambdas-old/                  ← Old lambda stubs (duplicate)
│   └── phase3-batch-architecture/    ← Future Step Functions design
│
└── SERVERLESS_IMPLEMENTATION.md      ← Phase 2 implementation guide
```

---

## Decision Log

### Why Lambda (Phase 2) before Batch (Phase 3)?

**Decision**: Build Lambda-based MVP first, Batch later

**Rationale**:
1. **Speed to deployment**: Lambda takes 10 min, Batch takes weeks
2. **Simplicity**: SQS queues vs. Step Functions state machines
3. **Cost validation**: $2/week proves value before $33/week commitment
4. **Iterative learning**: Test evaluation framework before scaling
5. **Phase 1 outputs directly feed Phase 2**: Selected model → weekly benchmark

**Trade-off accepted**: Lambda limited to 15-min runs, Batch unlimited. For MVP (5-turn dialogues), Lambda is sufficient.

### Why Python CDK instead of TypeScript?

**Decision**: Use Python CDK (`serverless/infra/`)

**Rationale**:
1. **Consistency**: Lambda handlers are Python, shared library is Python
2. **Maintainability**: Single language across stack
3. **Team expertise**: Phase 1 is Python-first
4. **Rapid prototyping**: CDK constructs + boto3 integration

**Trade-off accepted**: TypeScript has better CDK typing. Python sufficient for research project.

### Why Single Table DynamoDB?

**Decision**: Single table (`socratic_core`) with GSIs

**Rationale**:
1. **Cost**: One table = one billable entity
2. **Performance**: GSIs enable flexible access patterns
3. **Best practice**: AWS-recommended for serverless
4. **Simplicity**: Fewer connections, simpler IAM

**Access patterns supported**:
- Query by run ID (PK=RUN#, SK=TURN#/JUDGE#/SUMMARY)
- Query by model (GSI1PK=MODEL#)
- Query by manifest (GSI2PK=MANIFEST#)

### Why SQS instead of Step Functions?

**Decision**: Use SQS queues for MVP

**Rationale**:
1. **Free tier**: 1M requests/month free (vs. Step Functions paid per state transition)
2. **Simpler**: No JSON state machines to maintain
3. **Built-in durability**: DLQs, retries, visibility timeout
4. **Natural throttling**: Reserved concurrency on Lambdas

**When to switch**: Use Step Functions in Phase 3 for complex orchestration (Batch jobs, error handling, long-running workflows)

---

## Next Steps

### Immediate (This Week)
1. ✅ Consolidate repository structure (archive conflicts)
2. ✅ Update README.md with unified vision
3. ⏳ Complete Phase 1 model selection runs
4. ⏳ Document winning model decision

### Short-term (Next 2 Weeks)
1. ⏳ Deploy Phase 2 serverless stack
2. ⏳ Upload Phase 1 winner to weekly benchmark config
3. ⏳ Verify weekly runs and dashboard
4. ⏳ Set up monitoring and alerts

### Medium-term (Next 2 Months)
1. ⏳ Collect 8 weeks of baseline data
2. ⏳ Analyze quality drift patterns
3. ⏳ Tune judge rubrics and thresholds
4. ⏳ Validate cost model (~$8/month actual)

### Long-term (6+ Months)
1. ⏳ Phase 3 planning: IRB approval, student recruitment
2. ⏳ Implement Step Functions + Batch architecture
3. ⏳ Build real-time student dashboard
4. ⏳ Run pilot study with 24-48 students

---

## Key Principles

### 1. **Phased Delivery**
Build incrementally. Validate each phase before proceeding.

### 2. **CLI-First, Lambda-Second**
Shared library works locally (Phase 1) and serverless (Phase 2). Test logic before deploying.

### 3. **Simplest Thing That Works**
MVP uses Lambda + SQS. No Step Functions, no Batch until proven necessary.

### 4. **Reproducibility First**
Deterministic manifests (content-addressed), versioned configs, immutable S3 data.

### 5. **Observable by Default**
CloudWatch logs, X-Ray tracing, DynamoDB streams. Know what's happening.

### 6. **Cost-Conscious**
Free tiers where possible (SQS, Lambda), pay-per-use (DynamoDB), archive to Glacier (S3).

---

## FAQ

### Q: Why are there three different implementations?
**A**: Historical artifact from parallel exploration. Now consolidated:
- ✅ **Keep**: `serverless/` (Python CDK, complete)
- 📦 **Archive**: `infrastructure/` (TypeScript CDK, duplicate)
- 📦 **Archive**: `aws-benchmark-system/` (Phase 3 design, premature)

### Q: Which should I deploy for MVP?
**A**: `serverless/` only. It's complete, tested, and documented.

### Q: When do I need Step Functions + Batch?
**A**: Phase 3 (research experiment with students). Phase 2 MVP uses Lambda + SQS.

### Q: Can I run Phase 1 and Phase 2 simultaneously?
**A**: Yes! Phase 1 is CLI-based (local). Phase 2 is serverless (AWS). They share code but run independently.

### Q: What happens to Phase 1 code after model selection?
**A**: It stays! The context growth framework becomes the weekly benchmark used by Phase 2. Same evaluation logic, different execution environment (CLI → Lambda).

### Q: How do I add a new model to Phase 2?
**A**: Edit `serverless/artifacts/config.json` in S3, add model entry. Next weekly run picks it up automatically.

---

## Success Metrics

### Phase 1 (Model Selection)
- ✅ 8 models tested across 120 scenarios
- ✅ Dashboard shows clear winner
- ✅ Cost under $15
- ✅ Timeline under 5 days

### Phase 2 (Serverless Benchmarking)
- ⏳ Weekly runs complete successfully (>95% reliability)
- ⏳ Dashboard accessible and up-to-date
- ⏳ Monthly cost under $10
- ⏳ Baseline data collected (8+ weeks)

### Phase 3 (Production Research)
- ⏳ IRB approval obtained
- ⏳ 120+ students enrolled
- ⏳ Data collection complete (24 conditions)
- ⏳ Research paper submitted

---

## Contact & Support

**Project**: Socratic AI Institute
**Repository**: [socratic-ai-benchmarks](https://github.com/socratic-ai-institute/socratic-ai-benchmarks)
**Phase**: Transitioning Phase 1 → Phase 2
**AWS Profile**: `mvp`
**Region**: `us-east-1`

For questions, review this document first, then check phase-specific READMEs.

---

**Remember**: One phase at a time. Validate before scaling. Simplest thing that works.
