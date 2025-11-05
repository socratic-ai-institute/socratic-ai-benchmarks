# Socratic AI Benchmarks

**Automated evaluation framework for Socratic AI question generation**

[![Phase](https://img.shields.io/badge/Phase-1%20→%202%20Transition-blue)]()
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20Lambda%20%7C%20CDK-orange)]()
[![License](https://img.shields.io/badge/License-Research-yellow)]()

---

## Overview

This repository implements a **three-phase research project** to evaluate and deploy Socratic AI for educational interventions:

- **[Phase 1](#phase-1-model-selection-current)**: CLI-based model comparison (Select best model)
- **[Phase 2](#phase-2-serverless-benchmarking-mvp-ready)**: Serverless weekly benchmarking (Continuous evaluation)
- **[Phase 3](#phase-3-production-research-future)**: Production research study (120-240 students)

📖 **[Read the complete vision and roadmap →](VISION.md)**

---

## Quick Start

### Phase 1: Model Selection (Current Phase)

Compare models on Socratic question quality as context windows grow.

```bash
cd phase1-model-selection

# Run context growth evaluation
python -m socratic_eval.context_growth.runner \
  --models "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --test-types "consistency,complexity"

# Generate dashboard
python -m socratic_eval.context_growth.generate_dashboard \
  results.json --output dashboard.html
```

📂 **[Phase 1 README →](phase1-model-selection/README.md)**

---

### Phase 2: Serverless Benchmarking (MVP Ready)

Deploy automated weekly benchmarking platform.

```bash
cd serverless/infra

# Deploy infrastructure
cdk bootstrap  # First time only
cdk deploy

# Upload config
aws s3 cp config.json s3://$BUCKET_NAME/artifacts/config.json

# Trigger test run
aws lambda invoke --function-name SocraticBenchStack-PlannerFunction response.json
```

📂 **[Phase 2 README →](serverless/README.md)**
📖 **[Deployment Guide →](serverless/DEPLOYMENT_GUIDE.md)**
🚀 **[Quick Start →](serverless/QUICK_START.md)**

**Cost**: ~$2/week, ~$8/month

---

## Repository Structure

```
socratic-ai-benchmarks/
│
├── VISION.md                         ← 📖 Master plan (read this first!)
├── README.md                         ← This file
│
├── phase1-model-selection/           ← Phase 1: CLI model comparison
│   ├── socratic_eval/
│   │   ├── context_growth/           ← Context growth framework
│   │   ├── vectors.py                ← Three-vector evaluation
│   │   └── grader.py                 ← LLM-as-judge utilities
│   ├── benchmark.py
│   └── README.md
│
├── serverless/                       ← Phase 2: Serverless benchmarking MVP
│   ├── infra/                        ← Python CDK infrastructure
│   ├── lambdas/                      ← 5 Lambda functions
│   ├── lib/                          ← Shared library
│   ├── ui/                           ← Static dashboard
│   ├── scripts/                      ← Deployment helpers
│   └── README.md
│
├── archive/                          ← Superseded implementations
│   ├── infrastructure-typescript/    ← Old TypeScript CDK (don't use)
│   ├── lambdas-old/                  ← Old stubs (don't use)
│   └── phase3-batch-architecture/    ← Future design docs
│
└── SERVERLESS_IMPLEMENTATION.md      ← Phase 2 implementation summary
```

---

## Phase 1: Model Selection (Current)

### Objective
Select the best AWS Bedrock model for generating Socratic questions.

### Approach
- **Context Growth Framework**: Test how models maintain Socratic behavior as context windows grow
- **Three-Vector Evaluation**: Elenchus (refutation), Maieutics (discovery), Aporia (perplexity)
- **5 Core Metrics**: Persistence, Cognitive Depth, Context Adaptability, Resistance to Drift, Memory Preservation

### Status
✅ Framework complete and working
⏳ Running comparison tests

### Output
Model selection decision with quality scores, cost analysis, and deployment recommendation

**[Full Phase 1 Documentation →](phase1-model-selection/README.md)**

---

## Phase 2: Serverless Benchmarking (MVP Ready)

### Objective
Build automated weekly benchmarking system for continuous model evaluation.

### Architecture

```
EventBridge (weekly) → Planner Lambda → SQS dialogue-jobs
                                           ↓
                                      Runner Lambda (parallel)
                                           ↓
                                      SQS judge-jobs
                                           ↓
                                      Judge Lambda (parallel)
                                           ↓
                                      EventBridge run.judged
                                           ↓
                                      Curator Lambda
                                           ↓
                                      DynamoDB + S3
                                           ↓
                                      API Gateway + UI
```

### Key Features
- ✅ **All Lambda**: No containers, no servers
- ✅ **SQS Fan-Out**: Parallel execution with throttling
- ✅ **Single-Table DynamoDB**: Flexible queries with GSIs
- ✅ **Weekly Automated**: EventBridge cron trigger
- ✅ **API + Dashboard**: Real-time results

### Status
✅ Complete implementation ready to deploy

### Cost
- **Weekly run**: ~$2 (2 models × 6 scenarios)
- **Monthly**: ~$8
- **Idle**: ~$0.35 (storage only)

**[Full Phase 2 Documentation →](serverless/README.md)**

---

## Phase 3: Production Research (Future)

### Objective
Run full educational research study with 120-240 students testing location-aware Socratic AI.

### Status
📋 Design documents complete, implementation deferred until Phase 2 stable

### Architecture
**Different from Phase 2**: Step Functions + AWS Batch/Fargate (long-running jobs)

### Timeline
6-10 months after Phase 2 deployment

**[Phase 3 Design Docs →](archive/phase3-batch-architecture/)**

---

## Current Status

| Phase | Status | Next Action |
|-------|--------|-------------|
| **Phase 1** | ✅ Framework complete | Run full model comparison |
| **Phase 2** | ✅ MVP ready | Deploy infrastructure |
| **Phase 3** | 📋 Design only | Wait for Phase 2 stability |

**Current Focus**: Completing Phase 1 model selection, preparing Phase 2 deployment

---

## Key Documents

| Document | Purpose |
|----------|---------|
| **[VISION.md](VISION.md)** | Complete three-phase roadmap |
| **[phase1-model-selection/README.md](phase1-model-selection/README.md)** | Phase 1 documentation |
| **[serverless/README.md](serverless/README.md)** | Phase 2 architecture |
| **[serverless/DEPLOYMENT_GUIDE.md](serverless/DEPLOYMENT_GUIDE.md)** | Step-by-step deployment |
| **[SERVERLESS_IMPLEMENTATION.md](SERVERLESS_IMPLEMENTATION.md)** | Implementation summary |
| **[archive/README.md](archive/README.md)** | Why content was archived |

---

## Prerequisites

### Phase 1
- Python 3.9+
- AWS CLI configured with `mvp` profile
- AWS Bedrock access (Claude, Llama, Mistral models)

### Phase 2
- Python 3.12+
- Node.js 20+ (for CDK)
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS Account with Lambda, DynamoDB, S3, Bedrock access

---

## Key Principles

1. **Phased Delivery**: Build incrementally, validate before scaling
2. **CLI-First, Lambda-Second**: Test locally before deploying serverless
3. **Simplest Thing That Works**: Lambda + SQS for MVP, not Step Functions + Batch
4. **Reproducibility First**: Deterministic manifests, versioned configs, immutable data
5. **Observable by Default**: CloudWatch logs, X-Ray tracing, metrics
6. **Cost-Conscious**: Free tiers, pay-per-use, archive to cold storage

---

## Decision Log

### Why Lambda before Batch?
**Speed to value**: 10-minute deployment vs. weeks. $2/week validates approach before $33/week commitment.

### Why Python CDK?
**Consistency**: Single language across CLI, Lambda, and CDK. Easier maintenance.

### Why SQS before Step Functions?
**Simplicity + Cost**: Free tier covers 1M requests/month. No state machine JSON to maintain.

**[Full decision rationale →](VISION.md#decision-log)**

---

## FAQ

**Q: Which implementation should I deploy?**
**A**: `serverless/` only. Everything else is archived or future design.

**Q: Why are there archived directories?**
**A**: Historical artifacts from parallel exploration. Now consolidated on single MVP path.

**Q: Can I run Phase 1 and Phase 2 together?**
**A**: Yes! Phase 1 is CLI (local), Phase 2 is serverless (AWS). They share code but run independently.

**Q: When do I need Step Functions + Batch?**
**A**: Phase 3 (production research with students). Phase 2 MVP uses Lambda + SQS.

**[More FAQ →](VISION.md#faq)**

---

## Cost Estimates

### Phase 1: Model Selection
- **Full comparison** (8 models, 120 scenarios): ~$10
- **Quick test** (2 models, 10 scenarios): ~$1

### Phase 2: Serverless Benchmarking
- **Weekly run** (2 models, 6 scenarios): ~$2
- **Monthly total**: ~$8
- **Annual**: ~$100

### Phase 3: Production Research (Future)
- **Development**: ~$32K (16 weeks)
- **AWS infrastructure**: ~$440 (4 months)
- **Operational**: ~$8.7K (incentives, locations)
- **Total**: ~$41K

---

## Contributing

This is a research project. For improvements:

1. Open an issue describing the enhancement
2. Discuss approach (especially if changing data model)
3. Submit PR with tests and updated documentation

**Code style**: Black, isort, mypy

---

## License

Research code. License TBD pending publication.

---

## Contact

**Project**: Socratic AI Institute
**Repository**: [socratic-ai-benchmarks](https://github.com/socratic-ai-institute/socratic-ai-benchmarks)
**AWS Profile**: `mvp`
**Region**: `us-east-1`
**Current Phase**: 1 → 2 Transition

---

## Next Steps

### This Week
1. ✅ Consolidate repository (archive conflicts) ← **You are here**
2. ⏳ Complete Phase 1 model selection
3. ⏳ Document winning model

### Next 2 Weeks
4. ⏳ Deploy Phase 2 serverless stack
5. ⏳ Verify weekly benchmarks
6. ⏳ Set up monitoring

### Next 2 Months
7. ⏳ Collect baseline data (8+ weeks)
8. ⏳ Analyze quality drift patterns
9. ⏳ Plan Phase 3 research study

**📖 [See complete roadmap →](VISION.md)**

---

*Last Updated: 2025-11-05*
*Version: 2.0 (Unified)*
*Status: Phase 1 → Phase 2 Transition*
