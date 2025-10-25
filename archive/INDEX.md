# Socratic AI Benchmarks Platform - Documentation Index

**Last Updated:** October 23, 2025

---

## Quick Start

New to the project? Start here:

1. **[README.md](README.md)** - Project overview and research design
2. **[DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md)** - High-level data architecture overview
3. **[SCHEMA_QUICK_REFERENCE.md](SCHEMA_QUICK_REFERENCE.md)** - Quick patterns for common operations

---

## Documentation Structure

### 📊 Data Architecture (Primary Focus)

#### **[DYNAMODB_SCHEMA.md](DYNAMODB_SCHEMA.md)** (61 KB, ~51,000 words)
**Complete DynamoDB table design with detailed specifications**

**Contents:**
- Table structure (primary keys + 5 GSIs)
- All 8 entity schemas with example items
- Query patterns for all research questions
- DynamoDB code examples (Python)
- Analytics pipeline architecture
- Data integrity strategies
- Cost optimization

**When to use:**
- Implementing database operations
- Understanding entity structure
- Writing queries for research analysis
- Setting up DynamoDB Streams
- Configuring auto-scaling

---

#### **[types.ts](types.ts)** (24 KB, ~1,500 lines)
**TypeScript type definitions for type-safe development**

**Contents:**
- Complete TypeScript interfaces for all entities
- Helper types and enums
- Key builders for DynamoDB operations
- Validation functions
- Constants (locations, segments, questions)

**When to use:**
- Building frontend/backend in TypeScript
- Ensuring type safety across application
- Reference for entity attributes
- Building validation logic

---

#### **[dynamodb_helpers.py](dynamodb_helpers.py)** (29 KB, ~800 lines)
**Python library for database operations**

**Contents:**
- Complete CRUD operations for all entities
- Query helper functions using GSIs
- Learning gain calculations
- Type conversions (float ↔ Decimal)
- Example usage code

**When to use:**
- Building backend in Python
- Implementing data collection
- Running analytics queries
- Testing database operations

---

#### **[SCHEMA_QUICK_REFERENCE.md](SCHEMA_QUICK_REFERENCE.md)** (15 KB, ~14,000 words)
**Quick-reference guide for common patterns**

**Contents:**
- All 24 condition codes
- GSI usage examples
- Common query snippets (20+ examples)
- Metrics formulas
- Cost estimates
- Best practices checklist

**When to use:**
- Quick lookup during development
- Understanding condition codes
- Writing specific queries
- Calculating research metrics

---

#### **[ENTITY_RELATIONSHIPS.md](ENTITY_RELATIONSHIPS.md)** (23 KB, ~10,000 words)
**Visual diagrams and data flow charts**

**Contents:**
- Entity relationship diagrams (ASCII art)
- Data flow diagrams
- Intervention flow (dynamic vs static)
- Assessment flow
- Session state machine
- Research question → query mappings
- Aggregation pipeline architecture

**When to use:**
- Understanding system architecture
- Visualizing data relationships
- Planning new features
- Documenting for stakeholders

---

#### **[DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md)** (16 KB, ~14,000 words)
**High-level overview and implementation checklist**

**Contents:**
- Design philosophy and rationale
- All 24 experimental conditions
- Research questions supported
- Key metrics formulas
- Implementation checklist (5 phases)
- Cost estimates (~$31/month)
- Security & compliance notes

**When to use:**
- Project planning
- Stakeholder presentations
- Understanding design decisions
- Estimating costs and timelines

---

### 🎨 System Architecture

#### **[COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md)** (59 KB)
**Complete system architecture and component design**

**Contents:**
- Frontend components (React)
- Backend services (Node.js/Python)
- AWS infrastructure (Lambda, DynamoDB, S3)
- Authentication & authorization
- API design
- Deployment architecture

**When to use:**
- Understanding full system architecture
- Planning infrastructure
- Designing new components
- API integration

---

#### **[DASHBOARD_ARCHITECTURE.md](DASHBOARD_ARCHITECTURE.md)** (69 KB)
**Real-time analytics dashboard design**

**Contents:**
- Dashboard component hierarchy
- Real-time data visualization
- Researcher analytics views
- Session monitoring
- Condition comparison tools

**When to use:**
- Building analytics dashboards
- Understanding researcher workflows
- Designing visualizations
- Real-time data display

---

### 🚀 Deployment & Testing

#### **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** (27 KB)
**Complete deployment instructions**

**Contents:**
- Infrastructure as Code (CloudFormation/CDK)
- CI/CD pipeline setup
- Environment configuration
- Monitoring setup
- Rollback procedures

**When to use:**
- Setting up AWS infrastructure
- Deploying to production
- Configuring environments
- Setting up monitoring

---

#### **[TEST_AUTOMATION_STRATEGY.md](TEST_AUTOMATION_STRATEGY.md)** (80 KB)
**Comprehensive testing strategy**

**Contents:**
- Unit test patterns
- Integration test scenarios
- End-to-end test flows
- Data validation tests
- Performance testing

**When to use:**
- Writing test suites
- Validating data integrity
- Load testing
- Quality assurance

---

## File Size Summary

```
Total Documentation: ~400 KB

By Category:
├── Data Architecture:    ~152 KB (38%)
├── System Design:        ~128 KB (32%)
├── Testing:              ~80 KB  (20%)
├── Deployment:           ~27 KB  (7%)
└── Overview:             ~23 KB  (3%)
```

---

## Common Use Cases

### "I need to implement database operations"
**Read:**
1. [DYNAMODB_SCHEMA.md](DYNAMODB_SCHEMA.md) - Understand schema
2. [dynamodb_helpers.py](dynamodb_helpers.py) - Use helper functions
3. [types.ts](types.ts) - Type definitions

---

### "I need to build the frontend"
**Read:**
1. [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md) - System architecture
2. [types.ts](types.ts) - Type definitions
3. [DASHBOARD_ARCHITECTURE.md](DASHBOARD_ARCHITECTURE.md) - Dashboard design

---

### "I need to deploy to AWS"
**Read:**
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment steps
2. [DYNAMODB_SCHEMA.md](DYNAMODB_SCHEMA.md) - Table creation
3. [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md) - Infrastructure

---

### "I need to run research analytics"
**Read:**
1. [SCHEMA_QUICK_REFERENCE.md](SCHEMA_QUICK_REFERENCE.md) - Query patterns
2. [ENTITY_RELATIONSHIPS.md](ENTITY_RELATIONSHIPS.md) - Research questions
3. [dynamodb_helpers.py](dynamodb_helpers.py) - Analytics functions

---

### "I need to understand the experimental design"
**Read:**
1. [README.md](README.md) - Research design overview
2. [DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md) - Conditions & metrics
3. [ENTITY_RELATIONSHIPS.md](ENTITY_RELATIONSHIPS.md) - Data flows

---

### "I need to write tests"
**Read:**
1. [TEST_AUTOMATION_STRATEGY.md](TEST_AUTOMATION_STRATEGY.md) - Testing patterns
2. [dynamodb_helpers.py](dynamodb_helpers.py) - Example operations
3. [SCHEMA_QUICK_REFERENCE.md](SCHEMA_QUICK_REFERENCE.md) - Validation

---

## Quick Reference Tables

### Entity Types
| Entity | File | Lines | Use Case |
|--------|------|-------|----------|
| Student Profile | DYNAMODB_SCHEMA.md | 60-120 | Registration, consent |
| Session | DYNAMODB_SCHEMA.md | 140-240 | Core session data |
| Location Verification | DYNAMODB_SCHEMA.md | 260-330 | GPS/QR verification |
| Content Delivery | DYNAMODB_SCHEMA.md | 350-440 | Engagement tracking |
| Intervention (Dynamic) | DYNAMODB_SCHEMA.md | 460-640 | AI Socratic questions |
| Intervention (Static) | DYNAMODB_SCHEMA.md | 660-740 | Pre-written questions |
| Assessment | DYNAMODB_SCHEMA.md | 760-920 | Learning gain measurement |
| Post-Survey | DYNAMODB_SCHEMA.md | 940-1020 | Feedback collection |

---

### GSI Usage
| GSI | Purpose | File | Example Query |
|-----|---------|------|---------------|
| GSI1 | By Condition | SCHEMA_QUICK_REFERENCE.md | Compare conditions |
| GSI2 | By Student | SCHEMA_QUICK_REFERENCE.md | Student tracking |
| GSI3 | By Location | SCHEMA_QUICK_REFERENCE.md | Location analysis |
| GSI4 | By Intervention | SCHEMA_QUICK_REFERENCE.md | Static vs dynamic |
| GSI5 | By Date | SCHEMA_QUICK_REFERENCE.md | Daily reports |

---

### Key Metrics
| Metric | Formula | File |
|--------|---------|------|
| Absolute Gain | final - baseline | DATA_MODEL_SUMMARY.md |
| Normalized Gain | (final - baseline) / (100 - baseline) | DATA_MODEL_SUMMARY.md |
| Effect Size | (mean1 - mean2) / pooled_sd | SCHEMA_QUICK_REFERENCE.md |

---

## Experimental Conditions

**24 Total Conditions:**
```
4 Locations × 3 Intervals × 2 Intervention Types = 24

Locations:
1. on-site (Tredegar Iron Works)
2. learning-space (Lost Office Collaborative)
3. classroom (Richmond)
4. home

Intervals:
1. 2.5 minutes (4 interventions)
2. 5.0 minutes (2 interventions)
3. 10.0 minutes (1 intervention)

Intervention Types:
1. static (pre-written questions)
2. dynamic (AI Socratic dialogue)
```

**See:** [DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md#24-experimental-conditions)

---

## Research Questions

1. **Does location matter?**
   - Query: GSI3 (by location)
   - Analysis: ANOVA on learning gains

2. **Does intervention frequency matter?**
   - Query: Filter by interval
   - Analysis: ANOVA on learning gains

3. **Is dynamic AI better than static?**
   - Query: GSI4 (by intervention type)
   - Analysis: t-test, Cohen's d

4. **What are interaction effects?**
   - Query: GSI1 (all 24 conditions)
   - Analysis: Factorial ANOVA

5. **Does on-site amplify dynamic interventions?**
   - Query: GSI1 (specific 2×2)
   - Analysis: Interaction test

**See:** [ENTITY_RELATIONSHIPS.md](ENTITY_RELATIONSHIPS.md#dynamodb-access-patterns-by-research-question)

---

## Implementation Phases

### Phase 1: Infrastructure (Week 1)
- [ ] Create DynamoDB table
- [ ] Configure GSIs
- [ ] Set up Streams → Lambda → S3
- [ ] CloudWatch monitoring

**See:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

### Phase 2: Core Features (Weeks 2-4)
- [ ] Student registration
- [ ] Session management
- [ ] Location verification
- [ ] Content player
- [ ] Intervention system

**See:** [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md)

---

### Phase 3: Testing (Week 5)
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests
- [ ] Load tests

**See:** [TEST_AUTOMATION_STRATEGY.md](TEST_AUTOMATION_STRATEGY.md)

---

### Phase 4: Pilot (Week 6)
- [ ] 10 students
- [ ] 2-3 conditions
- [ ] Validate data
- [ ] Refine UX

**See:** [DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md#implementation-checklist)

---

### Phase 5: Full Launch (Week 7+)
- [ ] Balanced assignment across 24 conditions
- [ ] Real-time monitoring
- [ ] Data export for analysis

---

## Cost Estimates

**Monthly Operational Costs:**
```
DynamoDB:        $27.55  (88%)
Lambda:          $1.50   (5%)
S3:              $0.27   (1%)
CloudWatch:      $2.00   (6%)
─────────────────────────────
Total:           $31.32/month

Per session:     $0.01
```

**Assumptions:** 100 sessions/day, 3,000/month

**See:** [DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md#cost-estimates)

---

## Technology Stack

```
Frontend:
├── React (TypeScript)
├── Material-UI
├── Recharts (visualizations)
└── AWS Amplify (hosting)

Backend:
├── Node.js / Python
├── AWS Lambda (serverless)
├── API Gateway
└── DynamoDB

Infrastructure:
├── AWS CDK / CloudFormation
├── DynamoDB (single table)
├── S3 (exports)
├── CloudWatch (monitoring)
└── Athena (analytics)
```

---

## Getting Started Checklist

### For Developers
- [ ] Read [README.md](README.md)
- [ ] Review [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md)
- [ ] Study [DYNAMODB_SCHEMA.md](DYNAMODB_SCHEMA.md)
- [ ] Use [dynamodb_helpers.py](dynamodb_helpers.py) or [types.ts](types.ts)
- [ ] Follow [TEST_AUTOMATION_STRATEGY.md](TEST_AUTOMATION_STRATEGY.md)

### For Researchers
- [ ] Read [README.md](README.md)
- [ ] Review [DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md)
- [ ] Study [ENTITY_RELATIONSHIPS.md](ENTITY_RELATIONSHIPS.md)
- [ ] Use [SCHEMA_QUICK_REFERENCE.md](SCHEMA_QUICK_REFERENCE.md) for queries

### For DevOps
- [ ] Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [ ] Study [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md)
- [ ] Set up infrastructure per [DYNAMODB_SCHEMA.md](DYNAMODB_SCHEMA.md)
- [ ] Configure monitoring per [DATA_MODEL_SUMMARY.md](DATA_MODEL_SUMMARY.md)

---

## Support

### Documentation Issues
- Check this INDEX first
- Review relevant file(s) based on use case
- Cross-reference with QUICK_REFERENCE guides

### Implementation Questions
- Data operations → [dynamodb_helpers.py](dynamodb_helpers.py)
- Type definitions → [types.ts](types.ts)
- Query patterns → [SCHEMA_QUICK_REFERENCE.md](SCHEMA_QUICK_REFERENCE.md)
- Architecture → [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md)

---

## Document Map

```
socratic-ai-benchmarks/
│
├── INDEX.md                        ← You are here
├── README.md                       ← Start here
│
├── Data Architecture/
│   ├── DYNAMODB_SCHEMA.md          ← Primary schema reference
│   ├── types.ts                    ← TypeScript types
│   ├── dynamodb_helpers.py         ← Python helpers
│   ├── SCHEMA_QUICK_REFERENCE.md   ← Query patterns
│   ├── ENTITY_RELATIONSHIPS.md     ← Visual diagrams
│   └── DATA_MODEL_SUMMARY.md       ← Overview
│
├── System Design/
│   ├── COMPONENT_DIAGRAM.md        ← Full architecture
│   └── DASHBOARD_ARCHITECTURE.md   ← Analytics UI
│
├── Operations/
│   ├── DEPLOYMENT_GUIDE.md         ← Deploy to AWS
│   └── TEST_AUTOMATION_STRATEGY.md ← Testing guide
│
└── .claude-flow/                   ← Claude-Flow configs
```

---

**Last Updated:** October 23, 2025
**Total Documentation:** ~400 KB, 11 files
**Status:** Complete and ready for implementation
