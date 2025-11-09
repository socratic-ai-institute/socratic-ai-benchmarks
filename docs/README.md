# Socratic AI Benchmarks - Documentation Index

**Comprehensive guide to understanding and using the Socratic AI Benchmarking Platform**

This documentation suite provides everything you need to understand, deploy, and extend the platform for evaluating AI models' Socratic teaching abilities.

## 📚 Documentation Map

### For Different Audiences

#### 🌟 **Non-Technical Users**
Start here to understand what the project does and why it matters:
- [`/LAYPERSON_GUIDE.md`](/LAYPERSON_GUIDE.md) - Explains Socratic Method and why we're testing it
- [`/README.md`](/README.md) - Project overview with quick stats and links
- [`/VISION.md`](/VISION.md) - Long-term goals and research vision

#### 💻 **Developers & Engineers**
Technical documentation for understanding the codebase:
- [`/ARCHITECTURE.md`](/ARCHITECTURE.md) - System design and data flow
- [`/serverless/lib/socratic_bench/README.md`](/serverless/lib/socratic_bench/README.md) - Core library API
- [`/serverless/lambdas/README.md`](/serverless/lambdas/README.md) - Lambda functions reference
- [`/phase1-model-selection/socratic_eval/README.md`](/phase1-model-selection/socratic_eval/README.md) - Local testing tools

#### 🚀 **DevOps & Deployment**
Guides for deploying and managing the platform:
- [`/serverless/README.md`](/serverless/README.md) - Serverless platform overview
- [`/serverless/DEPLOYMENT_GUIDE.md`](/serverless/DEPLOYMENT_GUIDE.md) - Step-by-step deployment
- [`/CLOUD_DEPLOYMENT_PLAN.md`](/CLOUD_DEPLOYMENT_PLAN.md) - AWS infrastructure plan

#### 📊 **Researchers & Data Scientists**
Understanding the evaluation methodology:
- [`docs/benchmark.md`](benchmark.md) - Benchmark methodology
- [`/SCENARIOS.md`](/SCENARIOS.md) - Test scenarios in detail
- [`/DIMENSIONS_VS_VECTORS.md`](/DIMENSIONS_VS_VECTORS.md) - Scoring system explained
- [`/TERMINOLOGY_DOCUMENTATION.md`](/TERMINOLOGY_DOCUMENTATION.md) - Key concepts glossary

---

## 🎯 Quick Navigation by Task

### I want to...

#### **Understand the Project**
1. Read [`/README.md`](/README.md) for a quick overview
2. Read [`/LAYPERSON_GUIDE.md`](/LAYPERSON_GUIDE.md) for conceptual understanding
3. Read [`docs/benchmark.md`](benchmark.md) for methodology

#### **Deploy the Platform**
1. Read [`/serverless/README.md`](/serverless/README.md) for requirements
2. Follow [`/serverless/DEPLOYMENT_GUIDE.md`](/serverless/DEPLOYMENT_GUIDE.md)
3. Reference [`/CLOUD_DEPLOYMENT_PLAN.md`](/CLOUD_DEPLOYMENT_PLAN.md) for architecture

#### **Run Local Tests**
1. Read [`/phase1-model-selection/socratic_eval/README.md`](/phase1-model-selection/socratic_eval/README.md)
2. Install dependencies: `cd phase1-model-selection && pip install -r requirements.txt`
3. Run: `python -m socratic_eval.run_vectors`

#### **Add New Models**
1. Check [`docs/bedrock.md`](bedrock.md) for Bedrock setup
2. Add model to `/serverless/config-24-models.json`
3. Update `serverless/lib/socratic_bench/models.py` if new provider

#### **Add New Scenarios**
1. Review existing scenarios in `/SCENARIOS.md`
2. Edit `serverless/lib/socratic_bench/scenarios.py`
3. Follow the pattern: elenchus (contradiction), maieutics (discovery), aporia (misconception)

#### **Understand the Code**
1. Start with [`/serverless/lib/socratic_bench/README.md`](/serverless/lib/socratic_bench/README.md)
2. Read [`/ARCHITECTURE.md`](/ARCHITECTURE.md) for system design
3. Check [`/serverless/lambdas/README.md`](/serverless/lambdas/README.md) for Lambda details

#### **View Results**
1. Visit dashboard: https://d3ic7ds776p9cq.cloudfront.net
2. Review [`/BENCHMARKING_RESULTS_SUMMARY.md`](/BENCHMARKING_RESULTS_SUMMARY.md)
3. Check CloudWatch logs for detailed execution traces

---

## 📖 Core Documentation Files

### Project Overview & Vision

| Document | Purpose | Audience |
|----------|---------|----------|
| [`/README.md`](/README.md) | Main project README with quick start | Everyone |
| [`/LAYPERSON_GUIDE.md`](/LAYPERSON_GUIDE.md) | Non-technical explanation | Non-technical |
| [`/VISION.md`](/VISION.md) | Research vision and roadmap | Researchers |
| [`/TERMINOLOGY_DOCUMENTATION.md`](/TERMINOLOGY_DOCUMENTATION.md) | Glossary of terms | Everyone |

### Technical Architecture

| Document | Purpose | Audience |
|----------|---------|----------|
| [`/ARCHITECTURE.md`](/ARCHITECTURE.md) | System design and data flow | Engineers |
| [`docs/architecture.md`](architecture.md) | Detailed architecture diagrams | Engineers |
| [`/CLOUD_DEPLOYMENT_PLAN.md`](/CLOUD_DEPLOYMENT_PLAN.md) | AWS infrastructure plan | DevOps |
| [`/SERVERLESS_IMPLEMENTATION.md`](/SERVERLESS_IMPLEMENTATION.md) | Serverless design decisions | Engineers |

### Evaluation Methodology

| Document | Purpose | Audience |
|----------|---------|----------|
| [`docs/benchmark.md`](benchmark.md) | Benchmark methodology | Researchers |
| [`/SCENARIOS.md`](/SCENARIOS.md) | Test scenarios catalog | Researchers |
| [`/DIMENSIONS_VS_VECTORS.md`](/DIMENSIONS_VS_VECTORS.md) | Scoring system explained | Researchers |
| [`docs/runner.md`](runner.md) | Dialogue runner details | Engineers |

### Deployment & Operations

| Document | Purpose | Audience |
|----------|---------|----------|
| [`/serverless/README.md`](/serverless/README.md) | Serverless platform overview | DevOps |
| [`/serverless/DEPLOYMENT_GUIDE.md`](/serverless/DEPLOYMENT_GUIDE.md) | Step-by-step deployment | DevOps |
| [`/DEPLOYMENT_STATUS.md`](/DEPLOYMENT_STATUS.md) | Current deployment state | DevOps |
| [`docs/bedrock.md`](bedrock.md) | Bedrock setup guide | DevOps |

### Code Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [`/serverless/lib/socratic_bench/README.md`](/serverless/lib/socratic_bench/README.md) | Core library API reference | Engineers |
| [`/serverless/lambdas/README.md`](/serverless/lambdas/README.md) | Lambda functions reference | Engineers |
| [`/phase1-model-selection/socratic_eval/README.md`](/phase1-model-selection/socratic_eval/README.md) | Phase 1 local tools | Engineers |

### Historical & Archive

| Document | Purpose | Audience |
|----------|---------|----------|
| [`/CHANGELOG.md`](/CHANGELOG.md) | Version history | Everyone |
| [`/REFACTORING_COMPLETE.md`](/REFACTORING_COMPLETE.md) | Major refactoring notes | Engineers |
| [`/REFACTOR_APPROACH.md`](/REFACTOR_APPROACH.md) | Refactoring strategy | Engineers |
| [`/UNIFICATION_PLAN.md`](/UNIFICATION_PLAN.md) | Scoring unification plan | Engineers |
| [`/BENCHMARKING_RESULTS_SUMMARY.md`](/BENCHMARKING_RESULTS_SUMMARY.md) | Historical results | Researchers |

---

## 🏗️ System Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACES                          │
│  Dashboard (CloudFront) • CLI Tools • AWS Console           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  SERVERLESS PLATFORM                         │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Planner  │→ │  Runner  │→ │  Judge   │→ │ Curator  │   │
│  │ Lambda   │  │  Lambda  │  │  Lambda  │  │  Lambda  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↓             ↓             ↓             ↓           │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Core Library (socratic_bench)              │    │
│  │  dialogue • judge • models • prompts • scenarios   │    │
│  └────────────────────────────────────────────────────┘    │
└───────────────────┬──────────────────┬──────────────────────┘
                    │                  │
        ┌───────────▼─────────┐   ┌───▼──────────┐
        │   AWS Bedrock       │   │  Data Layer  │
        │  (25+ AI Models)    │   │ S3 • DynamoDB│
        └─────────────────────┘   └──────────────┘
```

**Read More**: [`/ARCHITECTURE.md`](/ARCHITECTURE.md)

---

## 📊 Key Concepts

### The Socratic Method

> "I cannot teach anybody anything. I can only make them think." — Socrates

The Socratic Method involves:
1. **Asking questions** instead of providing answers
2. **Probing assumptions** to reveal contradictions
3. **Guiding discovery** without lecturing
4. **Maintaining humility** about one's own knowledge

**Read More**: [`/LAYPERSON_GUIDE.md`](/LAYPERSON_GUIDE.md)

### Three Test Vectors

1. **Elenchus** (Refutation): Surface contradictions in beliefs
2. **Maieutics** (Guided Discovery): Scaffold understanding stepwise
3. **Aporia** (Productive Puzzlement): Deconstruct misconceptions

**Read More**: [`/SCENARIOS.md`](/SCENARIOS.md), [`/DIMENSIONS_VS_VECTORS.md`](/DIMENSIONS_VS_VECTORS.md)

### Vector-Based Scoring

Each AI response is scored on three vectors (0.00-1.00 scale):

| Vector | What It Measures | Ideal Range |
|--------|------------------|-------------|
| **Verbosity** | Optimal length (50-150 tokens) | 0.80-1.00 |
| **Exploratory** | Probing depth & conceptual questioning | 0.70-1.00 |
| **Interrogative** | Question-asking behavior & quality | 0.80-1.00 |

**Overall Score** = Average of 3 vectors

**Read More**: [`/DIMENSIONS_VS_VECTORS.md`](/DIMENSIONS_VS_VECTORS.md), [`/serverless/lib/socratic_bench/README.md`](/serverless/lib/socratic_bench/README.md)

---

## 🚀 Getting Started Paths

### Path 1: Quick Understanding (10 minutes)
1. Read `/README.md` (5 min)
2. Visit dashboard: https://d3ic7ds776p9cq.cloudfront.net (5 min)
3. Skim `/LAYPERSON_GUIDE.md` (optional)

### Path 2: Local Testing (30 minutes)
1. Read `/phase1-model-selection/socratic_eval/README.md` (10 min)
2. Set up AWS credentials (5 min)
3. Run local benchmark (15 min)

### Path 3: Full Deployment (2-3 hours)
1. Read `/serverless/README.md` (15 min)
2. Read `/serverless/DEPLOYMENT_GUIDE.md` (15 min)
3. Deploy CDK stack (60-90 min)
4. Verify deployment (30 min)

### Path 4: Deep Dive Development (1-2 days)
1. Read `/ARCHITECTURE.md` (30 min)
2. Read `/serverless/lib/socratic_bench/README.md` (30 min)
3. Read `/serverless/lambdas/README.md` (30 min)
4. Explore codebase with inline comments (varies)
5. Run local tests and experiments (varies)

---

## 🔍 Finding What You Need

### By Component

**Core Library**: [`/serverless/lib/socratic_bench/README.md`](/serverless/lib/socratic_bench/README.md)
- Dialogue execution
- Vector-based scoring
- Multi-provider Bedrock support
- Scenario management
- Prompt engineering

**Lambda Functions**: [`/serverless/lambdas/README.md`](/serverless/lambdas/README.md)
- Planner (orchestration)
- Runner (dialogue execution)
- Judge (scoring)
- Curator (aggregation)
- API (data serving)

**Local Tools**: [`/phase1-model-selection/socratic_eval/README.md`](/phase1-model-selection/socratic_eval/README.md)
- CLI benchmark runner
- LLM-as-judge (deprecated)
- Phase 1 experiments

### By Topic

**AWS Bedrock**: [`docs/bedrock.md`](bedrock.md)
**Benchmarking**: [`docs/benchmark.md`](benchmark.md)
**Architecture**: [`docs/architecture.md`](architecture.md), [`/ARCHITECTURE.md`](/ARCHITECTURE.md)
**Dialogue Running**: [`docs/runner.md`](runner.md)
**Scenarios**: [`/SCENARIOS.md`](/SCENARIOS.md)
**Terminology**: [`/TERMINOLOGY_DOCUMENTATION.md`](/TERMINOLOGY_DOCUMENTATION.md)

---

## 💡 Common Questions

### How do I add a new model?
1. Check model availability in AWS Bedrock console
2. Add to `/serverless/config-24-models.json`
3. If new provider, update `serverless/lib/socratic_bench/models.py`
4. Redeploy: `cd serverless && ./DEPLOY.sh`

### How do I create a new test scenario?
1. Review existing scenarios in `/SCENARIOS.md`
2. Edit `serverless/lib/socratic_bench/scenarios.py`
3. Add to appropriate vector function (elenchus/maieutics/aporia)
4. Redeploy and test

### What's the cost of running benchmarks?
- **Weekly automated run**: ~$5.50 (48 dialogues)
- **Monthly cost**: ~$22
- **Per-model test**: ~$0.16 (8 scenarios)

**Read More**: [`/serverless/lambdas/README.md`](/serverless/lambdas/README.md#-execution-metrics)

### How do I access the results?
1. **Dashboard**: https://d3ic7ds776p9cq.cloudfront.net
2. **S3 Bucket**: `s3://socratic-bench-bucket/curated/`
3. **DynamoDB**: Table `SocraticBenchTable`
4. **API**: GET `/api/latest-rankings`

### Where are the logs?
- **CloudWatch Log Groups**: `/aws/lambda/SocraticBenchStack-*`
- **Lambda Insights**: Available if enabled
- **X-Ray Traces**: Available if enabled

---

## 🤝 Contributing

To contribute documentation:

1. **Fix typos/errors**: Edit directly and submit PR
2. **Add examples**: Include in relevant README or guide
3. **New features**: Document in code comments + README
4. **Architecture changes**: Update `/ARCHITECTURE.md`

---

## 📞 Support

For issues or questions:

1. **Conceptual questions**: Check [`/LAYPERSON_GUIDE.md`](/LAYPERSON_GUIDE.md)
2. **Technical questions**: Check relevant component README
3. **Deployment issues**: Review [`/serverless/DEPLOYMENT_GUIDE.md`](/serverless/DEPLOYMENT_GUIDE.md)
4. **Runtime errors**: Check CloudWatch logs

---

**Built to understand how AI can become a better Socratic guide** 🤔

*Last Updated: 2025-11-09*
*Documentation Version: 2.0.0*
