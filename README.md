# Socratic AI Benchmarks

**Purpose**: Two-phase research project to test location-aware Socratic AI interventions in education.

---

## Project Overview

This repository contains code and documentation for a **rigorous educational research study** testing whether AI-generated Socratic questions improve learning comprehension compared to static interventions, and whether physical location amplifies this effect.

### Research Question

**Does location-aware Socratic AI improve learning outcomes?**

Testing across:
- 4 locations (on-site, learning space, classroom, home)
- 3 timing intervals (every 2.5min, 5min, 10min)
- 2 intervention types (static vs dynamic AI)
- **= 24 experimental conditions**

---

## Two-Phase Approach

### **Phase 1: Model Selection** (Current Phase)

**Goal**: Identify the best AI model for Socratic question generation

**Timeline**: 5 days
**Budget**: ~$10
**Output**: Model selection decision

📂 **Directory**: `/phase1-model-selection/`

### **Phase 2: Research Experiment** (Future)

**Goal**: Run full educational research study for publication

**Timeline**: 16-20 weeks
**Budget**: ~$48K-52K
**Output**: Research paper + dataset

📂 **Directory**: `/phase2-research-experiment/`

---

## Quick Start

### **Phase 1: Model Selection** (Start Here!)

```bash
# 1. Request Bedrock access (AWS Console, 5 min)
# Go to: https://console.aws.amazon.com/bedrock
# Request: Claude, Llama, Mistral models

# 2. Generate test scenarios
cd phase1-model-selection
python generate_scenarios.py

# 3. Run quick validation (2 models, 10 scenarios, 5 min)
python benchmark.py --quick

# 4. Run full comparison (8 models, 120 scenarios, 60 min)
python benchmark.py

# 5. Generate dashboard
python generate_dashboard.py

# 6. Select winning model
```

**See**: [`phase1-model-selection/README.md`](phase1-model-selection/README.md) for detailed instructions

---

## Repository Structure

```
socratic-ai-benchmarks/
│
├── phase1-model-selection/          ← START HERE
│   ├── README.md                    Phase 1 overview
│   ├── QUICK_START.md               5-minute setup guide
│   ├── benchmark.py                 Model comparison script
│   ├── generate_scenarios.py        Create test data
│   ├── generate_dashboard.py        Visualize results
│   └── results/                     Output directory
│
├── phase2-research-experiment/      Future research platform
│   ├── README.md                    Phase 2 overview
│   ├── architecture/                AWS infrastructure docs
│   ├── implementation/              Deployment guides
│   └── analysis/                    Research analysis
│
├── archive/                         Outdated/superseded docs
│
└── README.md                        This file
```

---

## Phase 1: Model Selection (Current)

### Objective

Test **8 AWS Bedrock models** to identify the best one for generating Socratic questions.

### Models Tested

| Model | Provider | Why Test |
|-------|----------|----------|
| Claude 3.5 Sonnet v2 | Anthropic | Current best Claude |
| Claude 3 Opus | Anthropic | Highest quality |
| Claude 3.5 Haiku | Anthropic | Fast + affordable |
| Mistral Large | Mistral AI | Non-Anthropic alternative |
| Llama 3.1 70B | Meta | Open-source contender |
| Llama 3.1 8B | Meta | Ultra-cheap baseline |
| Mixtral 8x7B | Mistral AI | Efficient MoE |
| Claude 3 Sonnet | Anthropic | Previous generation |

### Evaluation Criteria

1. **Quality** (primary): Overall Socratic question quality (0-1 scale)
   - Open-ended (not yes/no)
   - Probing depth
   - Builds on previous answers
   - Age-appropriate
   - Content-relevant

2. **Latency**: Response time (p50, p95, p99)
3. **Cost**: Per-question cost
4. **Reliability**: Success rate (no timeouts/errors)

### Timeline

| Day | Task | Output |
|-----|------|--------|
| 1 | Request Bedrock access | Approval pending |
| 2 | Generate scenarios + quick test | Validation complete |
| 3 | Run full comparison | Results JSON |
| 4 | Generate dashboard + analyze | Selection decision |
| 5 | Document decision | Report ready |

### Budget

- Full comparison: ~$10.44
- 8 models × 120 scenarios = 960 generations
- 960 scoring calls (LLM-as-judge)

### Output

**Selection Report** documenting:
- Model rankings by quality
- Cost-quality tradeoffs
- Recommended model with rationale
- Projected costs for Phase 2

---

## Phase 2: Research Experiment (After Model Selection)

### Objective

Run full educational research study with 120-240 students to test if location-aware Socratic AI improves learning.

### Experimental Design

**24 Conditions** (4 × 3 × 2 factorial):

| Factor | Levels |
|--------|--------|
| **Location** | On-site (Tredegar), Learning space, Classroom (UR), Home |
| **Timing** | Every 2.5min (4×), Every 5min (2×), Every 10min (1×) |
| **Intervention** | Static questions, Dynamic AI (selected model) |

### Infrastructure

- AWS serverless (Lambda, DynamoDB, Bedrock, Amplify)
- Real-time dashboard for researchers
- Location verification (GPS, QR codes)
- Automated data collection
- Cost: ~$85-111/month during data collection

### Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Pre-work | 2 weeks | IRB, content, assessments |
| Infrastructure | 3 weeks | AWS deployment |
| Experiment Engine | 4 weeks | Student flow, interventions |
| AI Quality | 2 weeks | Prompt optimization |
| Dashboard | 2 weeks | Analytics interface |
| Pilot | 3 weeks | Beta test (24-48 students) |
| Production | 8 weeks | Full study (120-240 students) |
| Analysis | 4 weeks | Statistical analysis, paper |

**Total**: 28 weeks (~7 months)

### Budget

| Category | Cost |
|----------|------|
| Development (16 weeks) | $32,000 |
| AWS infrastructure (4 months) | $440 |
| Operational (incentives, locations) | $8,700 |
| **Total** | **$41,140** |

### Output

- Research paper for publication (AERA, Learning Sciences, etc.)
- Complete dataset (anonymized)
- Reusable platform for future studies

---

## Current Status

**Phase**: 1 (Model Selection)
**Stage**: Setup complete, awaiting Bedrock access
**Next Step**: Run quick validation test

### Completed

- ✅ Repository organized (Phase 1 / Phase 2)
- ✅ Test scenario generator
- ✅ Benchmark script (8 Bedrock models)
- ✅ Documentation (Quick Start, architecture)
- ✅ AWS credentials configured (`mvp` profile)

### In Progress

- 🔄 Requesting Bedrock model access (1-2 hours)

### Pending

- ⏳ Run validation test (2 models, 10 scenarios)
- ⏳ Run full comparison (8 models, 120 scenarios)
- ⏳ Generate dashboard and analyze results
- ⏳ Document model selection decision

---

## Key Documents

### Phase 1 (Model Selection)

| Document | Purpose |
|----------|---------|
| [`phase1-model-selection/README.md`](phase1-model-selection/README.md) | Phase 1 overview |
| [`phase1-model-selection/QUICK_START.md`](phase1-model-selection/QUICK_START.md) | 5-minute setup |
| [`BEDROCK_MODEL_COMPARISON.md`](BEDROCK_MODEL_COMPARISON.md) | Complete architecture |

### Phase 2 (Research Experiment)

| Document | Purpose |
|----------|---------|
| [`phase2-research-experiment/README.md`](phase2-research-experiment/README.md) | Phase 2 overview |
| [`AWS_DEPLOYMENT_PLAN.md`](AWS_DEPLOYMENT_PLAN.md) | Master implementation plan |
| [`DYNAMODB_SCHEMA.md`](DYNAMODB_SCHEMA.md) | Data model |
| [`DASHBOARD_ARCHITECTURE.md`](DASHBOARD_ARCHITECTURE.md) | Frontend design |
| [`TEST_AUTOMATION_STRATEGY.md`](TEST_AUTOMATION_STRATEGY.md) | Testing approach |

---

## Dependencies

### Phase 1

```bash
# Python 3.9+
pip install boto3

# AWS CLI configured with 'mvp' profile
aws configure --profile mvp
```

### Phase 2

- Node.js 20+ (for CDK and frontend)
- Python 3.12+ (for Lambda functions)
- AWS account with Bedrock, Amplify, DynamoDB access
- IRB approval for research with minors

---

## Contributing

This is a research project. Contributions are not currently accepted, but you may:

- Review methodology in [`AWS_DEPLOYMENT_PLAN.md`](AWS_DEPLOYMENT_PLAN.md)
- Suggest improvements via issues
- Cite in your own research (citation coming after publication)

---

## License

Research code and methodology. License TBD pending publication.

---

## Contact

**Research Team**: University of Richmond
**AWS Profile**: `mvp`
**Region**: `us-east-1`
**Phase**: 1 (Model Selection)
**Status**: Awaiting Bedrock access

---

## Next Actions

### Today

1. Request Bedrock model access (AWS Console, 5 min)
2. Run `python generate_scenarios.py` (1 min)
3. Wait for Bedrock approval email (1-2 hours)

### Tomorrow

4. Run `python benchmark.py --quick` (5 min validation)
5. Run `python benchmark.py` (60 min full comparison)
6. Analyze results and select winning model
7. Document decision for Phase 2

**See [`phase1-model-selection/QUICK_START.md`](phase1-model-selection/QUICK_START.md) for detailed instructions.**

---

*Last Updated: 2025-10-25*
*Phase: 1 - Model Selection*
*Version: 1.0*
