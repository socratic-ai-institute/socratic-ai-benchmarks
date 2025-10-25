# Phase 2: Research Experiment

**Goal**: Run full educational research study for publication

**Timeline**: 28 weeks (~7 months)
**Budget**: ~$41K-52K
**Output**: Research paper + dataset

**Status**: ⏸️ Paused pending Phase 1 completion

---

## Overview

This phase builds the complete research platform to test whether location-aware Socratic AI interventions improve learning comprehension across 24 experimental conditions.

### Research Question

**Does physical location amplify the effectiveness of AI-generated Socratic dialogue for learning?**

---

## Experimental Design

### 24 Conditions (4 × 3 × 2 Factorial)

| Factor | Levels |
|--------|--------|
| **Location** | 1. On-site (Tredegar Iron Works)<br>2. Learning space (collaborative environment)<br>3. Classroom (University of Richmond)<br>4. Home (student's environment) |
| **Timing Interval** | 1. Every 2.5 minutes (4 interventions)<br>2. Every 5 minutes (2 interventions)<br>3. Every 10 minutes (1 intervention) |
| **Intervention Type** | 1. Static (pre-written questions)<br>2. Dynamic (AI-generated, selected model) |

### Sample Size

- Target: 5-10 students per condition
- Total: 120-240 students
- Age range: 14-18 (grades 9-12)
- Location: Richmond, VA area

### Content

- 10-minute audio/text presentation
- Topic: Richmond history (Tredegar Iron Works)
- 4 segments at 2.5-minute intervals

### Assessments

- Baseline comprehension test (before content)
- Final comprehension test (after content + interventions)
- Learning gain = Final - Baseline

---

## Prerequisites (Before Starting Phase 2)

### From Phase 1

- [x] Model selection complete
- [ ] Winning model documented
- [ ] Cost projections validated
- [ ] Prompt templates optimized

### Research Readiness

- [ ] IRB approval obtained (University of Richmond)
- [ ] Content production complete (10-min audio + transcript)
- [ ] Assessments designed and piloted (baseline + final)
- [ ] Location partnerships secured (Tredegar, UR, learning space)
- [ ] Sample size determined (power analysis)

### Technical Readiness

- [ ] AWS account configured
- [ ] Budget approved ($41K-52K)
- [ ] Developer assigned (16 weeks)
- [ ] Project management tool set up

---

## Implementation Phases

### Phase 2A: Infrastructure (Weeks 1-3)

**Goal**: Deploy AWS serverless backend

**Components**:
- DynamoDB tables (sessions, interventions, assessments)
- Lambda functions (session management, AI generation)
- Bedrock integration (selected model from Phase 1)
- API Gateway (REST endpoints)
- Cognito (authentication)
- CloudWatch (monitoring)

**Deliverable**: Backend infrastructure deployed and tested

**Budget**: $50-100/month AWS costs

### Phase 2B: Experiment Engine (Weeks 4-7)

**Goal**: Build student-facing flow

**Components**:
- Content delivery (audio/text player with interval pauses)
- Location verification (GPS, QR codes, network detection)
- Intervention orchestrator (static vs dynamic)
- Assessment administration (baseline + final tests)
- Session state management

**Deliverable**: Complete student flow from consent to completion

**Budget**: Development time only

### Phase 2C: AI Quality (Weeks 8-9)

**Goal**: Optimize prompts for location context

**Components**:
- Location-aware prompt templates
- Expert review (history educator + Socratic method expert)
- A/B testing (if needed)
- Regression testing (quality validation)

**Deliverable**: Production-ready prompts achieving ≥4.0/5 quality

**Budget**: Expert consultant fees (~$5K)

### Phase 2D: Dashboard (Weeks 10-11)

**Goal**: Build researcher monitoring interface

**Components**:
- AWS Amplify frontend (React + TypeScript)
- Real-time session monitoring (live map, progress tracking)
- Condition analytics (24-condition comparison)
- Data export (CSV, JSON, Parquet)
- Quality monitoring

**Deliverable**: Dashboard for research team

**Budget**: Amplify hosting (~$15/month)

### Phase 2E: Pilot Testing (Weeks 12-14)

**Goal**: Validate with small sample

**Components**:
- Alpha test (10 internal testers)
- Beta test (24-48 students, 1-2 per condition)
- Data quality validation
- Bug fixes and iteration

**Deliverable**: Production-ready system

**Budget**: Pilot student incentives (~$1K)

### Phase 2F: Data Collection (Weeks 15-22)

**Goal**: Run full study with 120-240 students

**Components**:
- Student recruitment
- Scheduled sessions (all 4 locations)
- Real-time monitoring
- Data quality checks
- Incident response

**Deliverable**: Complete dataset

**Budget**: Student incentives ($7.2K), operational costs (~$2K)

### Phase 2G: Analysis (Weeks 23-26)

**Goal**: Statistical analysis and paper writing

**Components**:
- Data cleaning and validation
- 4×3×2 factorial ANOVA
- Effect size calculations (Cohen's d)
- Visualizations and tables
- Research paper draft

**Deliverable**: Research paper ready for submission

**Budget**: Analysis software, statistical consultant (~$2K)

---

## Technology Stack

### Frontend
- React 18.3 + TypeScript
- Vite (build tool)
- Tailwind CSS + shadcn/ui
- React Query (server state)
- Zustand (client state)
- Recharts + D3.js (visualizations)
- Leaflet (maps)

### Backend
- AWS Lambda (Node.js 20.x, Python 3.12)
- Amazon Bedrock (Claude 3.5 Sonnet or selected model)
- DynamoDB (NoSQL database)
- API Gateway (HTTP API)
- AppSync (GraphQL + real-time)
- S3 (media storage)
- CloudFront (CDN)
- Cognito (authentication)

### Infrastructure
- AWS CDK (TypeScript) - Infrastructure as Code
- GitHub Actions - CI/CD
- CloudWatch - Monitoring
- X-Ray - Tracing

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [`AWS_DEPLOYMENT_PLAN.md`](AWS_DEPLOYMENT_PLAN.md) | Master implementation blueprint |
| [`DYNAMODB_SCHEMA.md`](DYNAMODB_SCHEMA.md) | Complete data model |
| [`DASHBOARD_ARCHITECTURE.md`](DASHBOARD_ARCHITECTURE.md) | Frontend design |
| [`TEST_AUTOMATION_STRATEGY.md`](TEST_AUTOMATION_STRATEGY.md) | Testing approach |
| [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) | Step-by-step AWS setup |

---

## Budget Breakdown

| Category | Cost |
|----------|------|
| **Development** (1 FT dev × 16 weeks) | $32,000 |
| **Consultants** (IRB, assessment, expert review) | $5,000 |
| **Content Production** (audio, transcript) | $2,000 |
| **AWS Infrastructure** (4 months) | $440 |
| **Student Incentives** (240 × $30) | $7,200 |
| **Location Partnerships** | $500 |
| **Operational** (printing, devices, misc) | $500 |
| **Contingency** (10%) | $4,764 |
| **TOTAL** | **$52,404** |

### Monthly AWS Costs (During Data Collection)

| Service | Usage | Cost/Month |
|---------|-------|------------|
| Lambda | 100 students × 100 invocations | $40 |
| Bedrock | 100 × 12 questions × $0.009 | $11 |
| DynamoDB | 5K writes + 20K reads | $6 |
| Amplify | Hosting + builds | $16 |
| S3 + CloudFront | 20GB + 100GB transfer | $11 |
| AppSync | Real-time subscriptions | $10 |
| CloudWatch | Logs + metrics | $5 |
| **Total** | | **$99/month** |

---

## Timeline (28 Weeks)

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 0-2 | Pre-work | IRB, content, assessments |
| 1-3 | Infrastructure | AWS deployment |
| 4-7 | Experiment Engine | Student flow complete |
| 8-9 | AI Quality | Prompts optimized |
| 10-11 | Dashboard | Researcher interface |
| 12-14 | Pilot | Beta test (24-48 students) |
| 15-22 | Data Collection | Full study (120-240 students) |
| 23-26 | Analysis | Statistical analysis, paper draft |

**Total**: ~7 months from IRB to paper submission

---

## Success Criteria

### Technical
- [ ] Uptime ≥99.5% during data collection
- [ ] Data loss rate = 0%
- [ ] API latency p95 <500ms
- [ ] Session completion rate ≥85%
- [ ] Cost per session $1-3

### Research
- [ ] Sample size achieved (≥120 students)
- [ ] Condition balance (chi-square p>0.05)
- [ ] Data quality ≥90% complete records
- [ ] Assessment reliability ≥0.80
- [ ] Statistically significant findings (p<0.05)

### Publication
- [ ] Research paper draft complete
- [ ] Dataset documented and anonymized
- [ ] Methodology reproducible
- [ ] IRB compliance verified
- [ ] Submitted to target journal

---

## Risk Mitigation

### IRB Delays
- **Mitigation**: Submit early, use expedited review
- **Contingency**: Build infrastructure while pending

### Content Quality
- **Mitigation**: Expert review, pilot testing
- **Contingency**: Iterate based on feedback

### Location Access
- **Mitigation**: Written partnerships, backup locations
- **Contingency**: Reduce to 3 locations (12 conditions)

### Recruitment Failure
- **Mitigation**: Multiple channels, attractive incentives
- **Contingency**: Extend timeline, lower sample size

### Cost Overrun
- **Mitigation**: Real-time monitoring, budget alerts
- **Contingency**: Switch to cheaper AI model, reduce sample

---

## Next Steps (After Phase 1 Completion)

1. **Review Phase 1 results**
   - Confirm winning model selection
   - Validate cost projections
   - Review any quality concerns

2. **Begin Pre-work** (Week 0-2)
   - Submit IRB protocol
   - Commission content production
   - Design assessments
   - Secure location partnerships

3. **Hold Gate 1 Decision Meeting**
   - Approve budget
   - Confirm timeline
   - Assign developer
   - Set up project tracking

4. **Deploy Infrastructure** (Week 1-3)
   - Follow [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)
   - Use selected model from Phase 1
   - Configure AWS environment
   - Run smoke tests

---

## Expected Outcomes

### Research Contributions

1. **Novel Findings**: First study testing location amplification of AI tutoring
2. **Methodological Innovation**: Rigorous 24-condition design with location verification
3. **Practical Impact**: Evidence for/against location-based learning interventions
4. **Reusable Platform**: Open-source code for future educational AI research

### Publication Targets

- AERA (American Educational Research Association)
- Journal of Learning Sciences
- Computers & Education
- Educational Technology Research & Development
- CHI (Human-Computer Interaction)

---

## Current Status

**Phase 2 Status**: ⏸️ **Paused**

**Awaiting**:
- ✅ Phase 1 model selection completion
- ⏳ Model selection decision documented
- ⏳ IRB protocol submission
- ⏳ Content production planning
- ⏳ Budget approval

**Next Milestone**: Gate 1 Decision Meeting (after Phase 1 complete)

---

*Last Updated: 2025-10-25*
*Status: Paused pending Phase 1 completion*
*Version: 1.0*
