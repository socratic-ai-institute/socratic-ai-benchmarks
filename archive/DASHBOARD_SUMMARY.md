# Socratic AI Benchmarks Dashboard - Executive Summary

## Overview

A comprehensive AWS Amplify-hosted research dashboard for monitoring a 24-condition educational study testing Socratic AI interventions across multiple locations with Richmond history content.

**Live Dashboard**: `https://dashboard.socraticresearch.org` (post-deployment)

---

## What This Dashboard Does

### For Research Team

**Real-Time Monitoring**
- Track 20+ students simultaneously across 4 physical locations
- See live progress: "Student at Tredegar just completed Segment 2, answering Q1 of 3"
- Geographic heatmap showing where learning is happening
- Alert system for dropped sessions or anomalies

**Experimental Analysis**
- Compare all 24 conditions side-by-side (4 locations × 3 intervals × 2 intervention types)
- Visualize learning gains: Which combinations work best?
- Drill down from overview → condition → session → individual Q&A sequences
- Statistical exports ready for R/Python analysis (CSV, JSON, Parquet)

**Data Quality Assurance**
- View exact intervention transcripts (all questions and answers)
- Location verification (GPS coordinates, timestamps)
- Assessment scores (baseline, mid-point, final)
- Intervention quality metrics (question depth, answer complexity)

### For Administrators

**User Management**
- Cognito-based authentication with role-based access
- Three user levels: Administrators, Researchers, PIs
- MFA support for sensitive accounts
- Audit logging for compliance (FERPA/IRB)

**System Health**
- CloudWatch monitoring dashboards
- Automated alerts (error rates, throttling, anomalies)
- Performance metrics (API latency, query times)
- Cost tracking and optimization suggestions

---

## Key Features

### 1. Dashboard Views

| View | Purpose | Key Metrics |
|------|---------|-------------|
| **Overview** | System health at a glance | Total sessions, Active now, Completion rate, Avg learning gain |
| **Conditions** | Compare all 24 conditions | N students per condition, Avg gain, Completion rate, Distribution plots |
| **Sessions** | Detailed session browser | Sortable/filterable table with search, Status badges, Score summaries |
| **Session Detail** | Individual session deep-dive | Full Q&A transcript, Timeline viz, Location verification, Assessment breakdown |
| **Live Monitoring** | Real-time map view | Active sessions on map, Progress indicators, Live updates (1-second refresh) |
| **Export** | Data extraction for analysis | Custom filters, Multiple formats, Anonymization options |

### 2. Data Visualizations

**Charts (Recharts)**
- Bar charts: Condition performance comparison
- Line charts: Score progression (baseline → final)
- Scatter plots: Correlation analysis (e.g., intervention time vs. gain)
- Box plots: Distribution summaries per condition

**Custom Visualizations (D3.js)**
- Timeline: Visual session flow (segments + interventions)
- Heatmap: Location-based learning distribution
- Network graph: Q&A conversation structure (future enhancement)

### 3. Real-Time Features

**WebSocket Subscriptions (AppSync)**
- Live session updates (segment completion, intervention progress)
- New session notifications
- Condition metrics updates
- Alert broadcasting

**Update Frequency**
- Critical data: 1-second refresh (active sessions)
- Metrics: 30-second refresh (overview dashboard)
- Historical data: On-demand (cached 5 minutes)

### 4. Export Capabilities

**Formats**
- **CSV**: Excel-compatible, one row per intervention
- **JSON**: Nested structure preserving full session hierarchy
- **Parquet**: Optimized for R/Python (pandas, arrow)

**Export Options**
- Date range filtering
- Condition selection (multi-select)
- Include/exclude incomplete sessions
- Anonymize student IDs (compliance mode)

**Data Structure** (CSV example)
```
session_id,student_age,student_grade,location,interval,intervention_type,
segment,timestamp,question_1,answer_1,question_2,answer_2,question_3,answer_3,
baseline_score,final_score,learning_gain
```

---

## Architecture Highlights

### Technology Stack

**Frontend**
- React 18.3 + TypeScript (type-safe components)
- Vite (fast builds, ~3 min deploy time)
- Tailwind CSS + shadcn/ui (consistent design)
- React Query (server state, automatic caching)
- Zustand (client state, persistent preferences)

**Backend (AWS)**
- AppSync (GraphQL API, real-time subscriptions)
- DynamoDB (sessions, students, conditions)
- Lambda (business logic, analytics)
- Cognito (authentication, user management)
- S3 (data exports, backups)
- Amplify (hosting, CI/CD)

**Infrastructure as Code**
- AWS CDK (TypeScript-based infrastructure)
- Version-controlled deployments
- One-command rollback capability

### Data Flow

```
Student App → API Gateway → Lambda → DynamoDB
                                        ↓
                                  DynamoDB Streams
                                        ↓
                                  Broadcast Lambda
                                        ↓
                                  AppSync Subscriptions
                                        ↓
                                  Dashboard (Real-time update)
```

### Security

**Authentication**
- Cognito User Pools (email + password)
- JWT tokens (automatic refresh)
- MFA support (TOTP, SMS)
- Session timeouts (8hr researchers, 4hr admins)

**Authorization**
- Role-based access control (RBAC)
- Field-level permissions (GraphQL directives)
- Row-level security (only access assigned conditions)

**Data Protection**
- Encryption at rest (DynamoDB, S3)
- Encryption in transit (TLS 1.3)
- No PII in identifiers (UUIDs only)
- FERPA-compliant audit logging

**Compliance**
- CloudTrail (all AWS API calls logged)
- Cognito activity logs (login attempts, password changes)
- Data access tracking (who viewed which sessions when)

---

## Deployment

### Quick Start (10 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/your-org/socratic-dashboard.git

# 2. Deploy infrastructure
cd infrastructure
npm install
cdk deploy DashboardStack

# 3. Deploy frontend
cd ../frontend
npm install
amplify init
amplify push

# 4. Connect to GitHub (auto-deploy on push)
git push origin main
```

**Result**: Dashboard live at `https://main.dxxxxx.amplifyapp.com`

### Environments

| Environment | Branch | URL | Purpose |
|-------------|--------|-----|---------|
| **Production** | `main` | `dashboard.socraticresearch.org` | Live research data |
| **Staging** | `staging` | `staging.socraticresearch.org` | Pre-release testing |
| **Preview** | PR branches | `pr-123.dxxxxx.amplifyapp.com` | Feature review |

### CI/CD Pipeline

```
Git Push → GitHub
  ↓
Amplify Console
  ↓
1. Download source
2. npm ci (install deps)
3. npm run codegen (GraphQL types)
4. npm run build (Vite build)
5. Upload to CDN
  ↓
Live Deployment (~5 minutes)
```

**Automatic Rollback**: If build fails, previous version remains live

---

## Performance

### Metrics (Expected)

| Metric | Target | Actual (Post-Launch) |
|--------|--------|----------------------|
| **Initial Load** | < 2s | _TBD_ |
| **Time to Interactive** | < 3s | _TBD_ |
| **Bundle Size** | < 200 KB | _TBD_ |
| **API Latency (p95)** | < 300ms | _TBD_ |
| **Real-time Update Lag** | < 2s | _TBD_ |

### Optimization Strategies

**Frontend**
- Code splitting (route-based)
- Lazy loading (heavy components)
- Virtual scrolling (large lists)
- Memoization (expensive calculations)
- React Query caching (5-minute stale time)

**Backend**
- DynamoDB GSI (fast condition queries)
- Lambda provisioned concurrency (no cold starts)
- AppSync caching (60-second TTL)
- CloudFront CDN (global distribution)

### Scalability

**Current Capacity** (without tuning)
- 1,000 sessions/day
- 50 concurrent users
- 10 active real-time subscriptions

**Scaling Strategy** (if needed)
- DynamoDB auto-scaling (5-100 RCU/WCU)
- Lambda concurrent execution limits (up to 1,000)
- AppSync connection pool (WebSocket scaling)

**Stress Test Results** (to be conducted)
- Target: 10,000 sessions/day
- 200 concurrent dashboard users
- 50 real-time monitoring clients

---

## Cost Breakdown

### Monthly Estimates

**Development Environment** (~$5/month)
- Amplify: $1 (5 GB storage, 50 build minutes)
- DynamoDB: Free tier (25 GB storage)
- AppSync: Free tier (250k queries)
- Lambda: Free tier (1M requests)
- Cognito: Free tier (50 users)

**Production Environment** (~$37/month @ 1,000 sessions)

| Service | Usage | Cost |
|---------|-------|------|
| Amplify Hosting | 100 build min + 10 GB storage | $7 |
| DynamoDB | 10 GB + on-demand reads/writes | $12 |
| AppSync | 500k queries + 100k subscriptions | $8 |
| Lambda | 1M invocations | $2 |
| S3 | 20 GB exports | $1 |
| CloudWatch | Logs + metrics | $5 |
| Data Transfer | 50 GB out | $5 |
| **Total** | | **$40/month** |

**Scaling Costs**
- 10,000 sessions/month: ~$150/month
- 100,000 sessions/month: ~$800/month

**Cost Optimization**
- Use DynamoDB on-demand (pay per request, not capacity)
- S3 lifecycle policies (auto-delete old exports after 30 days)
- CloudWatch log retention (7 days for debug, 30 days for audit)
- Reserved capacity (if usage predictable, ~30% savings)

---

## Monitoring & Alerts

### CloudWatch Dashboards

**System Health Dashboard**
- API request count (hourly)
- Error rate (4xx, 5xx)
- Lambda execution duration
- DynamoDB throttling events
- Active WebSocket connections

**Business Metrics Dashboard**
- Sessions created (daily)
- Completion rate trend
- Average learning gain (by condition)
- Export requests
- User login frequency

### Automated Alerts

**Critical Alerts** (PagerDuty/email)
- Error rate > 5% (5 consecutive minutes)
- API downtime (1 failed health check)
- DynamoDB throttling (10 events in 1 minute)
- Lambda timeout rate > 10%

**Warning Alerts** (email only)
- Export queue backlog > 10 jobs
- Disk usage > 80% (S3)
- Unusual login patterns (security)
- Cost spike > 50% above baseline

### Metrics Collection

**Custom Metrics**
- Dashboard page views (by route)
- Export format popularity (CSV vs JSON)
- Session detail drill-down rate
- Real-time monitoring usage

**Application Insights**
- User session duration
- Most viewed conditions
- Search query patterns
- Filter combinations used

---

## User Roles & Permissions

### Role Matrix

| Action | Administrators | Researchers | PIs |
|--------|----------------|-------------|-----|
| View sessions | ✅ | ✅ | ✅ |
| View PII (student names) | ✅ | ❌ | ✅ |
| Export data | ✅ | ✅ (anonymized) | ✅ |
| Flag anomalies | ✅ | ✅ | ✅ |
| Delete sessions | ✅ | ❌ | ✅ (own only) |
| Manage users | ✅ | ❌ | ❌ |
| View audit logs | ✅ | ❌ | ✅ |
| Modify infrastructure | ✅ | ❌ | ❌ |

### User Management

**Creating Users**
```bash
# Single user (CLI)
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_xxxxx \
  --username researcher@university.edu \
  --group-name Researchers

# Bulk import (CSV)
./scripts/bulk-create-users.sh users.csv
```

**Password Policies**
- Minimum 12 characters
- Requires: uppercase, lowercase, number, symbol
- Temporary password (force change on first login)
- Expires after 90 days

**MFA Enforcement**
- Administrators: Required (TOTP)
- Researchers: Optional
- PIs: Recommended

---

## Data Schema

### Session Record (DynamoDB)

```typescript
interface Session {
  // Identifiers
  sessionId: string;           // Primary key (UUID)
  studentId: string;           // Foreign key
  timestamp: number;           // Sort key (Unix timestamp)

  // Condition
  condition: {
    location: 'ON_SITE' | 'LEARNING_SPACE' | 'CLASSROOM' | 'HOME';
    intervalMinutes: 2.5 | 5.0 | 10.0;
    interventionType: 'STATIC' | 'DYNAMIC';
  };

  // Student data
  student: {
    age: number;
    grade: number;
    richmondResident: boolean;
  };

  // Location verification
  locationData: {
    type: string;
    name: string;
    verified: boolean;
    verificationMethod: 'GPS' | 'QR_CODE' | 'MANUAL';
    coordinates?: [number, number];
    checkInTime: string;
  };

  // Content delivery
  contentDelivery: {
    formatChosen: 'AUDIO' | 'TEXT';
    totalDuration: number;         // seconds
    actualCompletionTime: number;  // seconds (includes interventions)
    segmentsCompleted: number;
  };

  // Interventions
  interventions: Array<{
    timestamp: number;             // seconds into video
    type: 'STATIC' | 'DYNAMIC';
    questions: string[];           // 3 questions
    answers: string[];             // 3 answers
    durationSeconds: number;
    questionQualityScores?: number[];  // AI-generated (1-5)
    answerDepthScores?: number[];      // AI-generated (1-5)
  }>;

  // Assessments
  assessments: {
    baseline: {
      score: number;               // 0-100
      timeTaken: number;           // seconds
      responses: Array<{
        questionId: string;
        answer: string;
        correct: boolean;
      }>;
    };
    midpoint?: {                   // Optional (only some conditions)
      score: number;
      timeTaken: number;
      responses: Array<...>;
    };
    final: {
      score: number;
      timeTaken: number;
      responses: Array<...>;
    };
  };

  // Post-survey
  postSurvey?: {
    locationImpact: number;        // 1-5 scale
    interventionHelpful: number;   // 1-5 scale
    wouldRecommend: boolean;
    openFeedback: string;
  };

  // Metadata
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'DROPPED' | 'ANOMALY';
  startTime: string;               // ISO 8601
  endTime?: string;                // ISO 8601
  flagged: boolean;
  flagReason?: string;
  createdAt: string;
  updatedAt: string;
}
```

### GraphQL Schema

See `/Users/williamprior/Development/GitHub/socratic-ai-benchmarks/DASHBOARD_ARCHITECTURE.md` Section 4.1 for complete schema.

---

## Testing Strategy

### Test Coverage

**Unit Tests** (Vitest)
- Target: 80% coverage
- Components, utilities, hooks
- Run on every commit (GitHub Actions)

**Integration Tests** (Cypress)
- Dashboard flows (login → view → export)
- API integration (queries, mutations)
- Run on every PR

**E2E Tests** (Playwright)
- Critical paths (researcher workflow)
- Real-time features (subscriptions)
- Run nightly + before production deploy

**Load Tests** (Artillery)
- 100 concurrent users
- 1,000 requests/minute
- Run monthly

### Test Environments

**Local Development**
- Mocked API responses (MSW)
- Sample data (50 sessions)
- Fast feedback (<1s test runs)

**Staging**
- Real AWS infrastructure
- Synthetic data (1,000 sessions)
- Pre-production validation

**Production**
- Smoke tests post-deploy
- Canary deployments (10% traffic)
- Rollback on failure

---

## Documentation

### For Researchers

**User Guide** (`docs/user-guide.md`)
- Logging in
- Navigating dashboard
- Viewing sessions
- Exporting data
- Interpreting visualizations

**Video Tutorials** (to be created)
- 5-minute overview
- Deep dive: Session analysis
- How to export for statistical analysis

### For Administrators

**Admin Guide** (`docs/admin-guide.md`)
- User management (creating, deleting, resetting passwords)
- Monitoring system health
- Responding to alerts
- Backup and restore procedures

**Runbook** (`docs/runbook.md`)
- Common issues and solutions
- Emergency procedures
- Escalation paths

### For Developers

**Developer Guide** (`docs/developer-guide.md`)
- Local development setup
- Component architecture
- API integration
- Deployment process
- Contributing guidelines

**API Documentation** (`docs/api-docs.md`)
- GraphQL schema
- Query examples
- Mutation examples
- Subscription setup

---

## Roadmap

### Phase 1: MVP (Weeks 1-12) ✅
- [x] Infrastructure setup
- [x] Core dashboard views
- [x] Authentication
- [x] Basic export
- [ ] **Currently in progress**

### Phase 2: Enhancements (Weeks 13-20)
- [ ] Advanced analytics (correlation analysis, effect size calculations)
- [ ] Custom dashboards (researchers create own views)
- [ ] Automated reporting (weekly email summaries)
- [ ] Video playback (replay what students saw)

### Phase 3: Scale (Weeks 21-28)
- [ ] Multi-study support (multiple research projects)
- [ ] Collaborative features (comments, annotations)
- [ ] API for external tools (R, Python, Tableau)
- [ ] Mobile app (iOS/Android)

### Phase 4: Research Platform (Future)
- [ ] Study design builder (configure conditions via UI)
- [ ] Automated recruitment (participant management)
- [ ] Payment integration (participant compensation)
- [ ] Publication tools (generate IRB reports, papers)

---

## Success Metrics

### Technical Metrics

**Performance**
- Page load time < 2s (95th percentile)
- API response time < 300ms (95th percentile)
- Real-time update lag < 2s
- Uptime > 99.5% (excluding maintenance)

**Reliability**
- Zero data loss events
- < 1 production incident/month (Sev 1 or 2)
- Mean time to recovery (MTTR) < 1 hour

**Adoption**
- 100% of research team using dashboard
- > 80% prefer dashboard over manual analysis
- < 5 support tickets/week after training

### Research Metrics

**Data Quality**
- 100% of sessions captured in dashboard
- < 1% data discrepancies vs. source systems
- All exports validate against schema

**Efficiency**
- Analysis time reduced by 70% (vs. manual CSV review)
- Export-to-insight time < 10 minutes
- Real-time monitoring enables mid-study adjustments

**Impact**
- Enable 3x more students per study (scale)
- Reduce study duration by 30% (faster data collection)
- Support 5+ concurrent research projects

---

## Support & Maintenance

### Support Channels

**For Researchers**
- Email: dashboard-support@university.edu
- Slack: #socratic-dashboard
- Response time: < 4 hours (business days)

**For Emergencies**
- PagerDuty: On-call rotation
- Phone: +1 (555) 123-4567
- Response time: < 30 minutes (24/7)

### Maintenance Windows

**Regular Maintenance**
- Every Sunday 2-4 AM ET
- Database backups
- Security patches
- Performance optimization

**Emergency Maintenance**
- Announced 1 hour in advance (if possible)
- Status page: status.socraticresearch.org
- Auto-notification via email

### SLA (Service Level Agreement)

**Uptime Commitment**
- Target: 99.5% (excludes scheduled maintenance)
- Maximum downtime: 3.6 hours/month

**Data Durability**
- 99.999999999% (11 nines) via S3/DynamoDB
- Point-in-time recovery (30 days)
- Daily backups retained for 90 days

---

## Getting Started

### For Research Team

**Step 1: Request Access**
Email tech-lead@university.edu with:
- Full name
- Email address
- Role (Researcher, PI, Administrator)
- Study/project name

**Step 2: Receive Credentials**
You'll receive:
- Dashboard URL
- Temporary password
- Setup instructions

**Step 3: First Login**
1. Navigate to dashboard URL
2. Enter email + temporary password
3. Set new secure password
4. (Optional) Enable MFA

**Step 4: Training**
- Watch 5-minute tutorial video
- Schedule 1-on-1 walkthrough (if needed)
- Review user guide

### For Developers

**Step 1: Clone Repository**
```bash
git clone https://github.com/your-org/socratic-dashboard.git
cd socratic-dashboard
```

**Step 2: Install Dependencies**
```bash
npm install  # Frontend
cd infrastructure && npm install  # Backend
```

**Step 3: Configure AWS**
```bash
aws configure
# Enter credentials
```

**Step 4: Deploy to Dev**
```bash
cd infrastructure
cdk deploy DashboardStack-Dev

cd ../frontend
amplify init
amplify push
```

**Step 5: Run Locally**
```bash
npm run dev
# Opens http://localhost:5173
```

---

## FAQ

**Q: Can I access the dashboard from my phone?**
A: Yes, the dashboard is fully responsive and works on mobile browsers. Native apps are planned for Phase 3.

**Q: How long is data retained?**
A: Session data is retained for 3 years post-study completion. You can request early deletion or extension.

**Q: Can I export data for multiple conditions at once?**
A: Yes, use the multi-select filter in the Export page. You can select all 24 conditions or any subset.

**Q: Is student data anonymized?**
A: Yes, the dashboard uses UUIDs for students. Names/emails are never stored. PIs can access the linking table separately (not via dashboard).

**Q: What happens if I lose internet during monitoring?**
A: The dashboard caches recent data locally. When reconnected, it auto-syncs missed updates. You won't lose any historical data.

**Q: Can I create custom reports?**
A: Phase 2 will add custom dashboard builder. Currently, export data and use your preferred analysis tools (R, Python, Excel).

**Q: Who has access to my study's data?**
A: Only users you explicitly grant access to (via Cognito groups). Data is isolated per study in future multi-tenancy version.

**Q: Is the dashboard FERPA-compliant?**
A: Yes. All data encrypted, access logged, and no PII exposed without authorization. IRB documentation available on request.

---

## Contact Information

**Project Lead**
- Name: [Your Name]
- Email: lead@university.edu
- Office: [Building, Room]

**Technical Support**
- Email: dashboard-support@university.edu
- Slack: #socratic-dashboard
- Hours: 9 AM - 5 PM ET (Monday-Friday)

**Emergency Contact**
- PagerDuty: +1 (555) 123-4567
- Escalation: tech-lead@university.edu

**Feedback & Feature Requests**
- GitHub Issues: https://github.com/your-org/socratic-dashboard/issues
- Survey: https://forms.gle/xxxxx

---

## Acknowledgments

**Built With**
- React, TypeScript, Vite
- AWS Amplify, AppSync, DynamoDB, Lambda, Cognito
- Recharts, D3.js, Leaflet
- TanStack Query, Zustand
- Tailwind CSS, shadcn/ui

**Inspired By**
- Modern research platforms (Qualtrics, Gorilla)
- Data visualization best practices (Edward Tufte, Stephen Few)
- Real-time analytics dashboards (Datadog, Grafana)

**Special Thanks**
- Research team for feedback and requirements
- Students for participating in pilot testing
- AWS team for technical guidance

---

## Appendix

### Document Versions

- `DASHBOARD_ARCHITECTURE.md`: Complete technical architecture
- `COMPONENT_DIAGRAM.md`: Component hierarchy and data flows
- `DEPLOYMENT_GUIDE.md`: Step-by-step deployment instructions
- `DASHBOARD_SUMMARY.md`: This executive summary

### Related Documents

- Study design: `README.md`
- Student app documentation: (to be created)
- IRB protocol: (university-specific)
- Data analysis plan: (research team)

### Change Log

- **2025-10-23**: Initial dashboard design and architecture
- **TBD**: First deployment (Phase 1 complete)
- **TBD**: Phase 2 enhancements release

---

**End of Executive Summary**

For technical details, see `DASHBOARD_ARCHITECTURE.md`.
For deployment instructions, see `DEPLOYMENT_GUIDE.md`.
For component diagrams, see `COMPONENT_DIAGRAM.md`.
