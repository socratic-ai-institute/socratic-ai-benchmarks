# Socratic AI Benchmarks Dashboard Architecture

## Executive Summary

Complete AWS Amplify dashboard for monitoring a 24-condition educational research study testing Socratic AI interventions across 4 locations, 3 timing intervals, and 2 intervention types with Richmond history content.

**Dashboard URL**: `https://socratic-research.amplifyapp.com`

---

## 1. Dashboard Features & User Flows

### 1.1 Core Features

#### Real-Time Session Monitoring
- **Active Sessions View**: Live dashboard showing currently running experiments
- **Student Progress Tracker**: Per-student completion status (baseline → segments → interventions → final)
- **Location Heatmap**: Geographic distribution of active/completed sessions
- **Alert System**: Notifications for dropped sessions, technical issues, or data anomalies

#### Experimental Condition Overview
- **24-Condition Matrix**: Visual grid showing (4 locations × 3 intervals × 2 intervention types)
- **Per-Condition Metrics**:
  - N students enrolled
  - N sessions completed
  - Average completion time
  - Dropout rate
  - Average comprehension gain

#### Results Visualization
- **Comprehension Scores**:
  - Baseline vs. Final by condition
  - Learning gains (Δ score) distribution
  - Mid-point assessment tracking (5-minute mark)
- **Intervention Quality Metrics**:
  - Question depth scores (AI-generated vs. static)
  - Answer complexity analysis
  - Response time distributions
  - Conversation coherence scores

#### Data Export & Analysis
- **Export Formats**: CSV, JSON, Parquet (for R/Python)
- **Statistical Ready**: Pre-formatted for ANOVA, mixed-effects models
- **Custom Queries**: SQL-like interface for ad-hoc analysis
- **Session Replay**: View exact Q&A sequences with timestamps

### 1.2 User Flows

#### Flow 1: Research Team Login → Overview
```
1. Researcher logs in (Cognito)
2. Dashboard loads with:
   - Total active sessions (live count)
   - Completion rate across all conditions
   - Top-performing conditions (by learning gain)
   - Recent alerts/issues
3. Navigation: Overview | Conditions | Sessions | Students | Export
```

#### Flow 2: Drill-Down Analysis
```
1. Click condition (e.g., "On-Site × 2.5min × Dynamic")
2. See condition-specific view:
   - N students (18 completed, 2 in-progress, 3 scheduled)
   - Average metrics (comprehension gain, intervention time, etc.)
   - Distribution plots (score gains, response times)
3. Click individual student ID
4. Session detail view:
   - Timeline visualization (segments + interventions)
   - Full Q&A transcript
   - Location verification data
   - Assessment scores (baseline, mid, final)
5. Export this session's data
```

#### Flow 3: Real-Time Monitoring
```
1. Navigate to "Live Sessions" tab
2. Map view shows:
   - Red pins: On-site (Tredegar)
   - Blue pins: Learning space (Lost Office)
   - Green pins: Classroom
   - Yellow pins: Home
3. Click pin → see student's current progress:
   - "Segment 2 complete, Intervention 2 in progress"
   - "Question 2 of 3 answered"
4. Real-time updates via WebSocket (1-second refresh)
```

#### Flow 4: Statistical Export
```
1. Navigate to "Export" tab
2. Select filters:
   - Date range
   - Conditions (multi-select)
   - Include/exclude incomplete sessions
   - Anonymize student IDs (yes/no)
3. Choose format: CSV | JSON | R-ready | Python Pickle
4. Generate export → download link
5. Data structure follows tidy data principles:
   - One row per intervention
   - Nested JSON for Q&A sequences
   - Separate table for assessments
```

---

## 2. Technology Stack

### 2.1 Frontend Framework: **React 18.3+** with TypeScript

**Rationale**:
- Industry standard for dashboards
- Excellent library ecosystem (D3, Recharts, React Query)
- Strong TypeScript support (type safety for complex data models)
- Amplify first-class React support
- Component reusability for 24 similar condition views

**Alternatives Considered**:
- Vue 3: Simpler but less mature enterprise dashboard libraries
- Angular: Overkill for research dashboard; steeper learning curve
- Next.js: Server-side rendering unnecessary for authenticated admin portal

### 2.2 State Management: **React Query + Zustand**

**React Query** (TanStack Query v5):
- Server state (API data, real-time updates)
- Automatic caching & background refetch
- Optimistic updates for filters/queries
- Built-in loading/error states

**Zustand**:
- Client state (UI filters, selected conditions, map view state)
- Lightweight (no boilerplate)
- DevTools integration
- Persisted state (dashboard preferences)

**Data Flow**:
```
API (AppSync/REST)
  → React Query (cache + fetch)
    → Components (read)

User Interaction
  → Zustand (local state)
    → Components (UI updates)
```

### 2.3 Real-Time Updates: **AWS AppSync GraphQL Subscriptions**

**Implementation**:
```graphql
subscription OnSessionUpdate($studentId: ID!) {
  onSessionUpdate(studentId: $studentId) {
    sessionId
    currentSegment
    interventionProgress {
      questionNumber
      answered
      timestamp
    }
    assessmentScores {
      baseline
      midpoint
      final
    }
  }
}
```

**Rationale**:
- Native Amplify integration
- Managed WebSocket infrastructure
- Fine-grained subscriptions (per-session, per-condition)
- Auto-reconnection handling
- ~1 second latency (acceptable for research dashboard)

**Alternatives Considered**:
- Pusher: Additional cost, vendor lock-in
- Socket.io: Requires custom server (defeats Amplify serverless)
- Polling: Wasteful for infrequent updates

### 2.4 Data Visualization: **Recharts + D3.js**

**Recharts** (80% of charts):
- Bar charts (condition comparisons)
- Line charts (score progressions)
- Scatter plots (correlation analysis)
- Box plots (distribution summaries)

**D3.js** (custom visualizations):
- Location heatmap (custom SVG)
- Timeline visualization (segment + intervention flow)
- Network graphs (Q&A conversation structure)
- Custom condition matrix grid

**Example Recharts Component**:
```tsx
<ResponsiveContainer width="100%" height={400}>
  <BarChart data={conditionData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="condition" />
    <YAxis label={{ value: 'Learning Gain', angle: -90 }} />
    <Tooltip />
    <Legend />
    <Bar dataKey="averageGain" fill="#8884d8" />
    <Bar dataKey="staticGain" fill="#82ca9d" />
  </BarChart>
</ResponsiveContainer>
```

### 2.5 UI Component Library: **Tailwind CSS + shadcn/ui**

**Tailwind CSS**:
- Utility-first styling
- Consistent design system
- Rapid prototyping
- Small bundle size (PurgeCSS)

**shadcn/ui**:
- Pre-built accessible components
- Radix UI primitives (a11y compliant)
- Customizable (own your components)
- Data tables, dialogs, select menus

**Key Components**:
- `DataTable` (session list with sorting/filtering)
- `Dialog` (session detail overlay)
- `Select` (condition filters)
- `Card` (metric tiles)
- `Tabs` (navigation)

---

## 3. Amplify Integration

### 3.1 Amplify Hosting Configuration

**`amplify.yml`**:
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
        - npm run codegen # GraphQL types
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*

  customHeaders:
    - pattern: '**/*.js'
      headers:
        - key: Cache-Control
          value: 'public, max-age=31536000, immutable'
    - pattern: '**/*.html'
      headers:
        - key: Cache-Control
          value: 'no-cache'
```

**Branch Deployments**:
- `main` → Production (`socratic-research.amplifyapp.com`)
- `staging` → Staging (`staging.socratic-research.amplifyapp.com`)
- `dev` → Development (`dev.socratic-research.amplifyapp.com`)

**Environment Variables**:
```bash
VITE_API_ENDPOINT=https://api.socratic-research.com/graphql
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxx
VITE_COGNITO_CLIENT_ID=xxxxx
VITE_APPSYNC_ENDPOINT=https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql
```

### 3.2 CI/CD Pipeline

**Automatic Triggers**:
- Push to `main` → Deploy to production (auto)
- Push to `staging` → Deploy to staging (auto)
- Pull request → Preview deployment + Cypress E2E tests

**Build Minutes**: ~3-5 minutes per deployment

**Rollback Strategy**:
- Amplify Console → "Redeploy this version" (instant rollback)
- Git revert → auto-redeploy

### 3.3 Custom Domain Setup

**Primary Domain**: `socratic-research.amplifyapp.com`

**Custom Domain** (if purchased):
```
dashboard.socraticresearch.org
  → CNAME → main.xxxxx.amplifyapp.com
```

**SSL/TLS**: Managed by AWS Certificate Manager (auto-renewal)

### 3.4 Performance Optimization

**Lazy Loading**:
```tsx
const SessionDetail = lazy(() => import('./components/SessionDetail'));
const DataExport = lazy(() => import('./components/DataExport'));
const Analytics = lazy(() => import('./components/Analytics'));
```

**Code Splitting**: Automatic via Vite/Rollup

**CDN Caching**:
- HTML: No cache (always fresh)
- JS/CSS: 1 year cache (content hashing)
- API responses: React Query cache (5 minutes stale time)

**Bundle Size Target**: < 200 KB initial load (gzipped)

---

## 4. API Integration

### 4.1 GraphQL API via AWS AppSync

**Schema Overview**:
```graphql
type Session {
  sessionId: ID!
  studentId: ID!
  condition: Condition!
  startTime: AWSDateTime!
  endTime: AWSDateTime
  status: SessionStatus!

  locationData: LocationData!
  student: Student!
  contentDelivery: ContentDelivery!
  interventions: [Intervention!]!
  assessments: Assessments!
  postSurvey: PostSurvey
}

type Condition {
  location: Location!       # ON_SITE, LEARNING_SPACE, CLASSROOM, HOME
  intervalMinutes: Float!   # 2.5, 5.0, 10.0
  interventionType: InterventionType!  # STATIC, DYNAMIC
}

type Intervention {
  timestamp: Int!
  type: InterventionType!
  questions: [String!]!
  answers: [String!]!
  durationSeconds: Int!
  questionQualityScores: [Float!]
  answerDepthScores: [Float!]
}

type Assessments {
  baseline: Assessment!
  midpoint: Assessment
  final: Assessment!
}

type Assessment {
  score: Int!          # 0-100
  timeTaken: Int!      # seconds
  responses: [Response!]!
}

# Queries
type Query {
  # List queries
  listSessions(filter: SessionFilter, limit: Int, nextToken: String): SessionConnection!
  listStudents(filter: StudentFilter): [Student!]!

  # Single resource queries
  getSession(sessionId: ID!): Session
  getStudent(studentId: ID!): Student

  # Analytics queries
  conditionMetrics(condition: ConditionInput!): ConditionMetrics!
  aggregateMetrics(dateRange: DateRangeInput): AggregateMetrics!
  activeSessionsCount: Int!
}

# Mutations
type Mutation {
  # Admin operations
  updateSession(sessionId: ID!, updates: SessionUpdateInput!): Session!
  flagSessionAnomaly(sessionId: ID!, reason: String!): Session!
  exportData(filter: ExportFilter!): ExportJob!
}

# Subscriptions (Real-time)
type Subscription {
  onSessionUpdate(sessionId: ID): Session
    @aws_subscribe(mutations: ["updateSession"])

  onNewSession: Session
    @aws_subscribe(mutations: ["createSession"])

  onConditionMetricsUpdate(condition: ConditionInput): ConditionMetrics
}

# Supporting types
enum SessionStatus {
  SCHEDULED
  IN_PROGRESS
  COMPLETED
  DROPPED
  ANOMALY
}

enum Location {
  ON_SITE
  LEARNING_SPACE
  CLASSROOM
  HOME
}

enum InterventionType {
  STATIC
  DYNAMIC
}

type ConditionMetrics {
  condition: Condition!
  nStudentsEnrolled: Int!
  nSessionsCompleted: Int!
  averageCompletionTime: Float!
  dropoutRate: Float!
  averageComprehensionGain: Float!
  comprehensionGainStdDev: Float!
  interventionDurationAvg: Float!
}

type AggregateMetrics {
  totalSessions: Int!
  activeSessions: Int!
  completionRate: Float!
  topCondition: Condition!
  bottomCondition: Condition!
  averageGainOverall: Float!
}
```

**Resolver Architecture**:
- **DynamoDB**: Primary data store (Sessions, Students, Interventions)
- **Lambda Functions**: Business logic (metrics calculation, data aggregation)
- **VTL Templates**: Simple field resolution (direct DynamoDB access)

**Example Query**:
```graphql
query DashboardOverview {
  aggregateMetrics(dateRange: { start: "2025-10-01", end: "2025-10-31" }) {
    totalSessions
    activeSessions
    completionRate
    averageGainOverall
    topCondition {
      location
      intervalMinutes
      interventionType
    }
  }

  listSessions(
    filter: { status: IN_PROGRESS }
    limit: 50
  ) {
    items {
      sessionId
      student { age, grade }
      condition { location, intervalMinutes, interventionType }
      currentSegment
      interventionProgress {
        questionNumber
        answered
      }
    }
  }
}
```

### 4.2 Alternative: REST API via API Gateway

**If GraphQL is Overkill**:

**Endpoints**:
```
GET  /sessions
GET  /sessions/:id
GET  /sessions/active
GET  /sessions/:id/interventions
GET  /students/:id
GET  /conditions/:location/:interval/:type/metrics
GET  /metrics/aggregate
POST /export
```

**OpenAPI Spec**: Available at `/api/docs`

**Authentication**: API Gateway Authorizer (Cognito token validation)

### 4.3 Authentication & Authorization

**AWS Cognito User Pools**:

**User Groups**:
- `Administrators`: Full access (all CRUD operations)
- `Researchers`: Read-only + export
- `PIs` (Principal Investigators): All data access, no deletion

**Cognito Configuration**:
```json
{
  "userPoolName": "socratic-research-users",
  "autoVerify": ["email"],
  "passwordPolicy": {
    "minimumLength": 12,
    "requireUppercase": true,
    "requireNumbers": true,
    "requireSymbols": true
  },
  "mfaConfiguration": "OPTIONAL",
  "emailVerificationSubject": "Socratic Research Dashboard Access"
}
```

**Authorization Rules** (AppSync):
```graphql
type Session
  @aws_cognito_user_pools(cognito_groups: ["Researchers", "Administrators", "PIs"])
{
  sessionId: ID!
  # ... fields
}

type Mutation {
  deleteSession(sessionId: ID!): Session
    @aws_cognito_user_pools(cognito_groups: ["Administrators"])
}
```

**Frontend Auth Flow**:
```tsx
import { Authenticator } from '@aws-amplify/ui-react';

export function App() {
  return (
    <Authenticator>
      {({ signOut, user }) => (
        <Dashboard user={user} onLogout={signOut} />
      )}
    </Authenticator>
  );
}
```

### 4.4 Data Privacy & Compliance

**Student Data Protection**:
- Student IDs: UUIDs (no PII in identifiers)
- Anonymous mode: Export without linking to student profiles
- Data retention: Configurable (e.g., 3 years post-study)
- FERPA compliance: Encryption at rest (DynamoDB encryption) and in transit (TLS 1.3)

**IRB Requirements**:
- Audit logging (CloudTrail) for all data access
- Data access request tracking (who viewed which sessions when)
- Consent tracking (store consent timestamps per student)

---

## 5. Component Architecture

### 5.1 Component Hierarchy

```
<App>
├── <Authenticator>          # Cognito login wrapper
├── <Layout>                 # Shell with nav + sidebar
│   ├── <Sidebar>            # Navigation menu
│   │   ├── Overview
│   │   ├── Conditions
│   │   ├── Sessions
│   │   ├── Students
│   │   └── Export
│   └── <MainContent>
│       └── <Router>
│           ├── /overview          → <OverviewDashboard>
│           ├── /conditions        → <ConditionMatrix>
│           ├── /conditions/:id    → <ConditionDetail>
│           ├── /sessions          → <SessionList>
│           ├── /sessions/:id      → <SessionDetail>
│           ├── /students/:id      → <StudentProfile>
│           ├── /live              → <LiveMonitoring>
│           └── /export            → <DataExport>
```

### 5.2 Key Components

#### OverviewDashboard
```tsx
interface OverviewDashboardProps {}

export function OverviewDashboard() {
  const { data: metrics } = useQuery({
    queryKey: ['aggregateMetrics'],
    queryFn: fetchAggregateMetrics,
    refetchInterval: 30000, // 30s refresh
  });

  const { data: activeSessions } = useSubscription({
    subscription: ON_SESSION_UPDATE,
  });

  return (
    <div className="grid grid-cols-4 gap-6">
      <MetricCard
        title="Total Sessions"
        value={metrics.totalSessions}
        trend="+12 today"
      />
      <MetricCard
        title="Active Now"
        value={activeSessions.length}
        realTime
      />
      <MetricCard
        title="Completion Rate"
        value={`${metrics.completionRate}%`}
        trend="+3% vs last week"
      />
      <MetricCard
        title="Avg Learning Gain"
        value={`${metrics.averageGainOverall} pts`}
      />

      <div className="col-span-4">
        <ConditionPerformanceChart data={metrics.byCondition} />
      </div>

      <div className="col-span-2">
        <RecentSessionsTable sessions={metrics.recentSessions} />
      </div>

      <div className="col-span-2">
        <LocationHeatmap sessions={activeSessions} />
      </div>
    </div>
  );
}
```

#### ConditionMatrix
```tsx
interface ConditionMatrixProps {}

export function ConditionMatrix() {
  const { data: conditions } = useQuery({
    queryKey: ['conditions'],
    queryFn: fetchAllConditions,
  });

  const locations = ['ON_SITE', 'LEARNING_SPACE', 'CLASSROOM', 'HOME'];
  const intervals = [2.5, 5.0, 10.0];
  const interventions = ['STATIC', 'DYNAMIC'];

  return (
    <div className="space-y-8">
      {locations.map(location => (
        <div key={location}>
          <h3>{location.replace('_', ' ')}</h3>
          <div className="grid grid-cols-6 gap-4">
            {intervals.flatMap(interval =>
              interventions.map(intervention => {
                const condition = conditions.find(c =>
                  c.location === location &&
                  c.intervalMinutes === interval &&
                  c.interventionType === intervention
                );

                return (
                  <ConditionCard
                    key={`${location}-${interval}-${intervention}`}
                    condition={condition}
                    onClick={() => navigate(`/conditions/${condition.id}`)}
                  />
                );
              })
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function ConditionCard({ condition }) {
  return (
    <Card className="p-4 cursor-pointer hover:shadow-lg transition">
      <div className="text-sm font-medium">
        {condition.intervalMinutes}min × {condition.interventionType}
      </div>
      <div className="text-2xl font-bold mt-2">
        {condition.nStudentsCompleted}
      </div>
      <div className="text-xs text-gray-500">students</div>
      <div className="mt-2 text-sm">
        Gain: <span className="font-semibold">
          {condition.averageComprehensionGain.toFixed(1)} pts
        </span>
      </div>
      <Progress
        value={condition.completionRate}
        className="mt-2"
      />
    </Card>
  );
}
```

#### SessionDetail
```tsx
interface SessionDetailProps {
  sessionId: string;
}

export function SessionDetail({ sessionId }) {
  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => fetchSession(sessionId),
  });

  if (!session) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2>Session {session.sessionId.slice(0, 8)}</h2>
          <p className="text-gray-500">
            {session.student.age}yo, Grade {session.student.grade} •
            {session.condition.location} •
            {session.condition.intervalMinutes}min intervals
          </p>
        </div>
        <Button onClick={() => exportSession(sessionId)}>
          Export Session
        </Button>
      </div>

      {/* Timeline Visualization */}
      <Card>
        <CardHeader>Session Timeline</CardHeader>
        <CardContent>
          <SessionTimeline
            segments={session.contentDelivery.segments}
            interventions={session.interventions}
            assessments={session.assessments}
          />
        </CardContent>
      </Card>

      {/* Scores */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          title="Baseline Score"
          value={session.assessments.baseline.score}
        />
        <MetricCard
          title="Final Score"
          value={session.assessments.final.score}
        />
        <MetricCard
          title="Learning Gain"
          value={session.assessments.final.score - session.assessments.baseline.score}
          trend="improvement"
        />
      </div>

      {/* Interventions */}
      <Card>
        <CardHeader>
          Interventions ({session.interventions.length})
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible>
            {session.interventions.map((intervention, idx) => (
              <InterventionAccordionItem
                key={idx}
                intervention={intervention}
                index={idx}
              />
            ))}
          </Accordion>
        </CardContent>
      </Card>

      {/* Q&A Transcript */}
      <Card>
        <CardHeader>Full Q&A Transcript</CardHeader>
        <CardContent>
          {session.interventions.map((intervention, idx) => (
            <div key={idx} className="mb-6">
              <div className="text-sm text-gray-500 mb-2">
                Intervention {idx + 1} @ {formatTime(intervention.timestamp)}
              </div>
              {intervention.questions.map((q, qIdx) => (
                <div key={qIdx} className="mb-4">
                  <div className="bg-blue-50 p-3 rounded">
                    <strong>Q{qIdx + 1}:</strong> {q}
                  </div>
                  <div className="bg-gray-50 p-3 rounded mt-2">
                    <strong>A{qIdx + 1}:</strong> {intervention.answers[qIdx]}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Quality: {intervention.questionQualityScores?.[qIdx]?.toFixed(1)} |
                    Depth: {intervention.answerDepthScores?.[qIdx]?.toFixed(1)}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Location Data */}
      <Card>
        <CardHeader>Location Verification</CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Location Type</p>
              <p className="font-medium">{session.locationData.type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Verification Method</p>
              <p className="font-medium">{session.locationData.verificationMethod}</p>
            </div>
            {session.locationData.coordinates && (
              <div className="col-span-2">
                <p className="text-sm text-gray-500">GPS Coordinates</p>
                <p className="font-mono text-sm">
                  {session.locationData.coordinates.join(', ')}
                </p>
                <MiniMap coordinates={session.locationData.coordinates} />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

#### LiveMonitoring
```tsx
export function LiveMonitoring() {
  const { data: activeSessions } = useSubscription({
    subscription: ON_SESSION_UPDATE,
  });

  const mapRef = useRef<MapRef>(null);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  return (
    <div className="grid grid-cols-3 gap-6 h-screen">
      {/* Map View */}
      <div className="col-span-2">
        <Card className="h-full">
          <CardHeader>
            <div className="flex justify-between items-center">
              <h3>Live Session Map</h3>
              <div className="text-sm text-gray-500">
                {activeSessions.length} active sessions
              </div>
            </div>
          </CardHeader>
          <CardContent className="h-full">
            <MapContainer
              center={[37.5407, -77.4360]} // Richmond, VA
              zoom={12}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

              {activeSessions.map(session => (
                <LocationMarker
                  key={session.sessionId}
                  session={session}
                  onClick={() => setSelectedSession(session.sessionId)}
                  color={getLocationColor(session.condition.location)}
                />
              ))}
            </MapContainer>
          </CardContent>
        </Card>
      </div>

      {/* Session List */}
      <div className="col-span-1 overflow-y-auto">
        <Card>
          <CardHeader>Active Sessions</CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activeSessions.map(session => (
                <ActiveSessionCard
                  key={session.sessionId}
                  session={session}
                  isSelected={selectedSession === session.sessionId}
                  onClick={() => setSelectedSession(session.sessionId)}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        {selectedSession && (
          <Card className="mt-4">
            <CardHeader>Session Details</CardHeader>
            <CardContent>
              <SessionProgress sessionId={selectedSession} />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function ActiveSessionCard({ session, isSelected, onClick }) {
  return (
    <div
      className={cn(
        "p-3 border rounded cursor-pointer transition",
        isSelected ? "border-blue-500 bg-blue-50" : "border-gray-200"
      )}
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="font-medium text-sm">
            {session.student.age}yo, Grade {session.student.grade}
          </div>
          <div className="text-xs text-gray-500">
            {session.condition.location} • {session.condition.intervalMinutes}min
          </div>
        </div>
        <div className="text-xs font-medium text-green-600">
          LIVE
        </div>
      </div>

      <Progress
        value={(session.currentSegment / 4) * 100}
        className="mt-2"
      />

      <div className="text-xs text-gray-500 mt-1">
        Segment {session.currentSegment} of 4
        {session.interventionProgress && (
          <> • Q{session.interventionProgress.questionNumber}/3</>
        )}
      </div>
    </div>
  );
}
```

#### DataExport
```tsx
export function DataExport() {
  const [filters, setFilters] = useState<ExportFilters>({
    dateRange: { start: null, end: null },
    conditions: [],
    includeIncomplete: false,
    anonymize: true,
  });

  const [format, setFormat] = useState<'csv' | 'json' | 'parquet'>('csv');

  const exportMutation = useMutation({
    mutationFn: (params: ExportParams) => requestExport(params),
    onSuccess: (job) => {
      toast.success('Export started! You will be notified when ready.');
      pollExportStatus(job.id);
    },
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>Export Configuration</CardHeader>
        <CardContent className="space-y-4">
          {/* Date Range */}
          <div>
            <Label>Date Range</Label>
            <DateRangePicker
              value={filters.dateRange}
              onChange={(range) => setFilters({ ...filters, dateRange: range })}
            />
          </div>

          {/* Condition Filter */}
          <div>
            <Label>Conditions (multi-select)</Label>
            <ConditionMultiSelect
              value={filters.conditions}
              onChange={(conditions) => setFilters({ ...filters, conditions })}
            />
          </div>

          {/* Options */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="incomplete"
                checked={filters.includeIncomplete}
                onCheckedChange={(checked) =>
                  setFilters({ ...filters, includeIncomplete: checked as boolean })
                }
              />
              <Label htmlFor="incomplete">Include incomplete sessions</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="anonymize"
                checked={filters.anonymize}
                onCheckedChange={(checked) =>
                  setFilters({ ...filters, anonymize: checked as boolean })
                }
              />
              <Label htmlFor="anonymize">Anonymize student IDs</Label>
            </div>
          </div>

          {/* Format */}
          <div>
            <Label>Export Format</Label>
            <RadioGroup value={format} onValueChange={setFormat}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="csv" id="csv" />
                <Label htmlFor="csv">CSV (Excel compatible)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="json" id="json" />
                <Label htmlFor="json">JSON (nested structure)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="parquet" id="parquet" />
                <Label htmlFor="parquet">Parquet (R/Python optimized)</Label>
              </div>
            </RadioGroup>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 p-4 rounded">
            <p className="text-sm text-gray-700">
              <strong>Estimated rows:</strong> ~{estimateRows(filters)}
            </p>
            <p className="text-sm text-gray-700">
              <strong>File size:</strong> ~{estimateSize(filters, format)}
            </p>
          </div>

          <Button
            onClick={() => exportMutation.mutate({ filters, format })}
            disabled={exportMutation.isPending}
            className="w-full"
          >
            {exportMutation.isPending ? 'Generating...' : 'Generate Export'}
          </Button>
        </CardContent>
      </Card>

      {/* Export History */}
      <Card>
        <CardHeader>Recent Exports</CardHeader>
        <CardContent>
          <ExportHistoryTable />
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## 6. Data Flow Diagrams

### 6.1 Real-Time Session Update Flow

```
Student App (Mobile/Web)
  ↓
  [POST] /sessions/:id/progress
  ↓
API Gateway / AppSync Mutation
  ↓
Lambda: UpdateSessionProgress
  ↓
DynamoDB: Update session record
  ↓
DynamoDB Stream
  ↓
Lambda: BroadcastUpdate
  ↓
AppSync Subscription (WebSocket)
  ↓
Dashboard (React)
  ↓
React Query Cache Update
  ↓
UI Re-render (LiveMonitoring component)
```

### 6.2 Dashboard Load Flow

```
User → Login → Cognito
  ↓
Cognito returns JWT token
  ↓
Dashboard loads → useQuery('aggregateMetrics')
  ↓
GraphQL query → AppSync
  ↓
AppSync → Lambda Resolver
  ↓
Lambda queries DynamoDB (Sessions table)
  ↓
Lambda aggregates metrics (avg scores, counts, etc.)
  ↓
Returns metrics → AppSync → Dashboard
  ↓
React Query caches result (5min stale time)
  ↓
Components render metrics
```

### 6.3 Export Flow

```
User configures export → clicks "Generate"
  ↓
Mutation: requestExport(filters, format)
  ↓
AppSync → Lambda: CreateExportJob
  ↓
Lambda writes job to DynamoDB (ExportJobs table)
  ↓
Lambda triggers Step Function
  ↓
Step Function orchestrates:
  1. Query sessions (paginated)
  2. Transform to format (CSV/JSON/Parquet)
  3. Write to S3 bucket
  4. Generate signed download URL (1hr expiry)
  5. Send email notification
  ↓
Dashboard polls export status (every 5s)
  ↓
When complete, show download link
```

---

## 7. Performance Optimization

### 7.1 Lazy Loading Strategy

```tsx
// Route-based code splitting
const routes = [
  {
    path: '/overview',
    component: lazy(() => import('./pages/Overview')),
  },
  {
    path: '/conditions',
    component: lazy(() => import('./pages/ConditionMatrix')),
  },
  {
    path: '/sessions/:id',
    component: lazy(() => import('./pages/SessionDetail')),
  },
  {
    path: '/export',
    component: lazy(() => import('./pages/DataExport')),
    preload: true, // Preload on hover
  },
];

// Component-level lazy loading
const HeavyChart = lazy(() => import('./components/HeavyChart'));

function Dashboard() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <HeavyChart data={data} />
    </Suspense>
  );
}
```

### 7.2 Caching Strategy

**React Query Configuration**:
```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 min
      cacheTime: 10 * 60 * 1000,     // 10 min
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Per-query overrides
useQuery({
  queryKey: ['aggregateMetrics'],
  queryFn: fetchMetrics,
  staleTime: 1 * 60 * 1000,  // 1 min for overview metrics
});

useQuery({
  queryKey: ['session', sessionId],
  queryFn: () => fetchSession(sessionId),
  staleTime: Infinity,  // Never refetch (static historical data)
});
```

**Browser Storage**:
```tsx
// Zustand persisted state
const useDashboardStore = create(
  persist(
    (set) => ({
      selectedConditions: [],
      dateRange: { start: null, end: null },
      viewPreferences: { theme: 'light', chartType: 'bar' },
    }),
    {
      name: 'dashboard-preferences',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
```

### 7.3 Optimistic UI Updates

```tsx
const updateSessionMutation = useMutation({
  mutationFn: (updates: SessionUpdate) => updateSession(updates),
  onMutate: async (updates) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['session', updates.sessionId] });

    // Snapshot current value
    const previousSession = queryClient.getQueryData(['session', updates.sessionId]);

    // Optimistically update
    queryClient.setQueryData(['session', updates.sessionId], (old) => ({
      ...old,
      ...updates,
    }));

    return { previousSession };
  },
  onError: (err, updates, context) => {
    // Rollback on error
    queryClient.setQueryData(
      ['session', updates.sessionId],
      context.previousSession
    );
  },
  onSettled: (data, error, updates) => {
    // Refetch to ensure consistency
    queryClient.invalidateQueries({ queryKey: ['session', updates.sessionId] });
  },
});
```

### 7.4 Virtual Scrolling for Large Lists

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function SessionList({ sessions }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: sessions.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // px per row
    overscan: 5,
  });

  return (
    <div ref={parentRef} className="h-screen overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <SessionCard session={sessions[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 8. Deployment Configuration

### 8.1 Infrastructure as Code (AWS CDK)

**`lib/dashboard-stack.ts`**:
```typescript
import * as cdk from 'aws-cdk-lib';
import * as amplify from 'aws-cdk-lib/aws-amplify';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as appsync from 'aws-cdk-lib/aws-appsync';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class DashboardStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Cognito User Pool
    const userPool = new cognito.UserPool(this, 'ResearcherPool', {
      userPoolName: 'socratic-research-users',
      selfSignUpEnabled: false, // Admin-created accounts only
      signInAliases: { email: true },
      autoVerify: { email: true },
      passwordPolicy: {
        minLength: 12,
        requireUppercase: true,
        requireLowercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      mfa: cognito.Mfa.OPTIONAL,
      mfaSecondFactor: {
        sms: true,
        otp: true,
      },
    });

    // User Groups
    new cognito.CfnUserPoolGroup(this, 'AdminGroup', {
      userPoolId: userPool.userPoolId,
      groupName: 'Administrators',
      description: 'Full dashboard access',
    });

    new cognito.CfnUserPoolGroup(this, 'ResearcherGroup', {
      userPoolId: userPool.userPoolId,
      groupName: 'Researchers',
      description: 'Read-only + export',
    });

    // DynamoDB Tables
    const sessionsTable = new dynamodb.Table(this, 'SessionsTable', {
      tableName: 'socratic-sessions',
      partitionKey: { name: 'sessionId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.NUMBER },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
      pointInTimeRecovery: true, // Data safety
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });

    // GSI for querying by student
    sessionsTable.addGlobalSecondaryIndex({
      indexName: 'byStudent',
      partitionKey: { name: 'studentId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.NUMBER },
    });

    // GSI for querying by condition
    sessionsTable.addGlobalSecondaryIndex({
      indexName: 'byCondition',
      partitionKey: { name: 'conditionKey', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.NUMBER },
    });

    // AppSync API
    const api = new appsync.GraphqlApi(this, 'DashboardAPI', {
      name: 'socratic-dashboard-api',
      schema: appsync.SchemaFile.fromAsset('graphql/schema.graphql'),
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.USER_POOL,
          userPoolConfig: { userPool },
        },
      },
      xrayEnabled: true, // Observability
      logConfig: {
        fieldLogLevel: appsync.FieldLogLevel.ERROR,
      },
    });

    // Data source
    const sessionsDataSource = api.addDynamoDbDataSource(
      'SessionsDataSource',
      sessionsTable
    );

    // Resolvers
    sessionsDataSource.createResolver('GetSessionResolver', {
      typeName: 'Query',
      fieldName: 'getSession',
      requestMappingTemplate: appsync.MappingTemplate.dynamoDbGetItem(
        'sessionId',
        'sessionId'
      ),
      responseMappingTemplate: appsync.MappingTemplate.dynamoDbResultItem(),
    });

    // Amplify Hosting
    const amplifyApp = new amplify.CfnApp(this, 'DashboardApp', {
      name: 'socratic-dashboard',
      repository: 'https://github.com/your-org/socratic-dashboard',
      accessToken: cdk.SecretValue.secretsManager('github-token').toString(),
      buildSpec: cdk.Fn.sub(`
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
        - npm run codegen
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
      `),
      environmentVariables: [
        {
          name: 'VITE_API_ENDPOINT',
          value: api.graphqlUrl,
        },
        {
          name: 'VITE_USER_POOL_ID',
          value: userPool.userPoolId,
        },
        {
          name: 'VITE_AWS_REGION',
          value: cdk.Stack.of(this).region,
        },
      ],
    });

    // Branch deployments
    new amplify.CfnBranch(this, 'MainBranch', {
      appId: amplifyApp.attrAppId,
      branchName: 'main',
      stage: 'PRODUCTION',
      enableAutoBuild: true,
      enablePullRequestPreview: true,
    });

    new amplify.CfnBranch(this, 'StagingBranch', {
      appId: amplifyApp.attrAppId,
      branchName: 'staging',
      stage: 'BETA',
      enableAutoBuild: true,
    });

    // Outputs
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPool.userPoolId,
    });

    new cdk.CfnOutput(this, 'GraphQLEndpoint', {
      value: api.graphqlUrl,
    });

    new cdk.CfnOutput(this, 'AmplifyAppId', {
      value: amplifyApp.attrAppId,
    });
  }
}
```

### 8.2 Environment Variables

**`.env.production`**:
```bash
VITE_API_ENDPOINT=https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxx
VITE_COGNITO_CLIENT_ID=xxxxx
VITE_MAPBOX_TOKEN=pk.xxxxx
```

**`.env.staging`**:
```bash
VITE_API_ENDPOINT=https://staging-xxxxx.appsync-api.us-east-1.amazonaws.com/graphql
# ... staging credentials
```

### 8.3 Monitoring & Alerts

**CloudWatch Alarms**:
```typescript
// API Error Rate
new cloudwatch.Alarm(this, 'APIErrorAlarm', {
  metric: api.metricError(),
  threshold: 10,
  evaluationPeriods: 1,
  alarmDescription: 'AppSync error rate too high',
  actionsEnabled: true,
});

// DynamoDB Throttling
new cloudwatch.Alarm(this, 'DynamoThrottleAlarm', {
  metric: sessionsTable.metricSystemErrorsForOperations({
    operations: [dynamodb.Operation.GET_ITEM, dynamodb.Operation.QUERY],
  }),
  threshold: 5,
  evaluationPeriods: 2,
});
```

**X-Ray Tracing**: Enabled on AppSync + Lambda for performance debugging

---

## 9. Wireframes & Visual Design

### 9.1 Overview Dashboard (Desktop)

```
┌─────────────────────────────────────────────────────────────────┐
│  Socratic Research Dashboard              👤 Admin  🔔  ⚙️     │
├─────────────────────────────────────────────────────────────────┤
│ [Overview] [Conditions] [Sessions] [Live] [Export]              │
├───────────┬─────────────────────────────────────────────────────┤
│           │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │
│           │  │ Total   │  │ Active  │  │Complete │  │ Avg    │ │
│ Sidebar:  │  │ 456     │  │ 23 🔴  │  │ 87.3%   │  │ Gain   │ │
│           │  │ sessions│  │ live    │  │ rate    │  │ +12.4  │ │
│ • Overview│  └─────────┘  └─────────┘  └─────────┘  └────────┘ │
│ • Conditns│                                                      │
│ • Sessions│  Condition Performance (Avg Learning Gain)          │
│ • Live Map│  ┌───────────────────────────────────────────────┐  │
│ • Export  │  │     ┃▇▇▇▇▇▇▇▇▇ On-Site×2.5m×Dynamic  +18.3   │  │
│           │  │     ┃▇▇▇▇▇▇▇  Learn×2.5m×Dynamic    +15.1   │  │
│ Filters:  │  │     ┃▇▇▇▇▇    Class×5m×Static       +9.2    │  │
│ [Date]    │  │     ┃▇▇▇      Home×10m×Static       +5.6    │  │
│ [Location]│  └───────────────────────────────────────────────┘  │
│ [Interval]│                                                      │
│           │  Recent Sessions              Location Distribution │
│           │  ┌──────────────────────┐    ┌────────────────────┐│
│           │  │ ID8a3 | 16yo | On-S │    │   🗺️  Richmond     ││
│           │  │ ✓ Complete | +22pts │    │   • Tredegar (12)  ││
│           │  │ ID9f2 | 15yo | Home │    │   • Lost Office(8) ││
│           │  │ ⏸ In Progress | Q2/3│    │   • Classroom (15) ││
│           │  │ IDa12 | 17yo | Learn│    │   • Home (18)      ││
│           │  │ ✓ Complete | +18pts │    │                    ││
│           │  └──────────────────────┘    └────────────────────┘│
└───────────┴─────────────────────────────────────────────────────┘
```

### 9.2 Condition Matrix View

```
┌─────────────────────────────────────────────────────────────────┐
│  24 Experimental Conditions                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ON-SITE (Tredegar Iron Works)                                  │
│  ┌────────────┬────────────┬────────────┬────────────┬────────┐ │
│  │  2.5m      │  2.5m      │  5.0m      │  5.0m      │ 10.0m  │ │
│  │  Static    │  Dynamic   │  Static    │  Dynamic   │ Static │ │
│  │────────────│────────────│────────────│────────────│────────│ │
│  │ 18 students│ 19 students│ 17 students│ 20 students│ 18 stu │ │
│  │ ✓ 18 done  │ ✓ 17 done  │ ✓ 16 done  │ ✓ 19 done  │ ✓ 17 d │ │
│  │ Gain: +9.2 │ Gain: +18.3│ Gain: +11.5│ Gain: +16.8│ Gain:+8│ │
│  │ ██████ 94% │ ███████ 89%│ ██████ 94% │ ████████95%│ ██████ │ │
│  └────────────┴────────────┴────────────┴────────────┴────────┘ │
│                                                                  │
│  LEARNING SPACE (Lost Office Collaborative)                     │
│  ┌────────────┬────────────┬────────────┬────────────┬────────┐ │
│  │  2.5m      │  2.5m      │  5.0m      │  5.0m      │ 10.0m  │ │
│  │  Static    │  Dynamic   │  Static    │  Dynamic   │ Static │ │
│  │────────────│────────────│────────────│────────────│────────│ │
│  │ 15 students│ 16 students│ 14 students│ 17 students│ 15 stu │ │
│  │ ✓ 14 done  │ ✓ 15 done  │ ✓ 13 done  │ ✓ 16 done  │ ✓ 14 d │ │
│  │ Gain: +10.1│ Gain: +15.1│ Gain: +12.3│ Gain: +14.7│ Gain:+9│ │
│  │ █████ 93%  │ ██████ 94% │ █████ 93%  │ ██████ 94% │ █████  │ │
│  └────────────┴────────────┴────────────┴────────────┴────────┘ │
│                                                                  │
│  [CLASSROOM and HOME sections follow same pattern...]           │
│                                                                  │
│  Click any card for detailed view →                             │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 Session Detail View

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Sessions                          [Export Session]   │
│                                                                  │
│  Session 8a3f4b2c                                               │
│  16yo, Grade 10 • ON-SITE • 2.5min Dynamic                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Timeline Visualization                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 0:00 ════ 2:30 ╪ 5:00 ╪ 7:30 ╪ 10:00                      │   │
│  │ Base  Seg1  I1  Seg2 I2 Seg3 I3 Seg4 I4  Final           │   │
│  │  ✓     ✓    ✓    ✓   ✓   ✓   ✓   ✓   ✓    ✓             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────┐  ┌───────────┐  ┌────────────┐                  │
│  │ Baseline  │  │ Final     │  │ Learning   │                  │
│  │ 52 / 100  │  │ 74 / 100  │  │ Gain: +22  │                  │
│  └───────────┘  └───────────┘  └────────────┘                  │
│                                                                  │
│  Interventions (4)                                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ▼ Intervention 1 @ 2:30                    Duration: 1:35│   │
│  │   ┌──────────────────────────────────────────────────┐   │   │
│  │   │ Q1: What stood out to you about the founding... │   │   │
│  │   │ A1: I thought it was interesting that...        │   │   │
│  │   │ Quality: 3.8  |  Depth: 2.1                     │   │   │
│  │   │                                                  │   │   │
│  │   │ Q2: Building on your observation about timing...│   │   │
│  │   │ A2: Well, I think the location near the river...│   │   │
│  │   │ Quality: 4.1  |  Depth: 3.2                     │   │   │
│  │   │                                                  │   │   │
│  │   │ Q3: How do you think Richmond's geography...    │   │   │
│  │   │ A3: The James River provided both power and...  │   │   │
│  │   │ Quality: 4.3  |  Depth: 3.8                     │   │   │
│  │   └──────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Location Verification                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Type: ON-SITE                                            │   │
│  │ Location: Tredegar Iron Works                            │   │
│  │ Verification: GPS (✓ Verified within 25m)               │   │
│  │ Coordinates: 37.5316, -77.4481                           │   │
│  │ [Mini map showing pin at Tredegar]                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 9.4 Live Monitoring Map View

```
┌─────────────────────────────────────────────────────────────────┐
│  Live Session Monitoring                     🔴 23 Active       │
├─────────────────────────────────────────────────────────────────┤
│                                   │                              │
│         🗺️  Richmond, VA          │  Active Sessions            │
│  ┌──────────────────────────────┐ │  ┌───────────────────────┐  │
│  │                              │ │  │ 🔴 ID 8a3f              │  │
│  │    🔵 Lost Office (3)        │ │  │ 16yo, Grade 10         │  │
│  │                              │ │  │ On-Site • 2.5m Dynamic │  │
│  │       🏛️                     │ │  │ Segment 3/4            │  │
│  │    🔴 Tredegar (5) ← Selected│ │  │ ████████░░ 80%         │  │
│  │                              │ │  │ Intervention in prog.  │  │
│  │                              │ │  ├───────────────────────┤  │
│  │   🟢 Classroom (7)           │ │  │ 🔴 ID 9f21             │  │
│  │                              │ │  │ 15yo, Grade 10         │  │
│  │                              │ │  │ Home • 5m Static       │  │
│  │  🟡 Home locations (8)       │ │  │ Segment 2/4            │  │
│  │     (scattered)              │ │  │ ████░░░░░░ 40%         │  │
│  │                              │ │  ├───────────────────────┤  │
│  └──────────────────────────────┘ │  │ ... (21 more)          │  │
│                                   │  └───────────────────────┘  │
│  Legend:                          │                              │
│  🔴 On-Site  🔵 Learning Space   │  Session Details:            │
│  🟢 Classroom  🟡 Home            │  ┌───────────────────────┐  │
│                                   │  │ Session 8a3f           │  │
│  Filters:                         │  │ Currently: Segment 3   │  │
│  [All Locations ▼]               │  │ Q2 of 3 in progress    │  │
│  [All Intervals ▼]               │  │                        │  │
│                                   │  │ Elapsed: 7:42          │  │
│  [Refresh: Auto 1s]              │  │ Estimated: 2:18 remain │  │
│                                   │  │                        │  │
│                                   │  │ Last answer received:  │  │
│                                   │  │ 12 seconds ago         │  │
│                                   │  └───────────────────────┘  │
└───────────────────────────────────┴──────────────────────────────┘
```

---

## 10. Testing Strategy

### 10.1 Unit Tests (Vitest + React Testing Library)

**Example: Component Test**
```tsx
// SessionCard.test.tsx
import { render, screen } from '@testing-library/react';
import { SessionCard } from './SessionCard';

describe('SessionCard', () => {
  const mockSession = {
    sessionId: '8a3f4b2c',
    student: { age: 16, grade: 10 },
    condition: {
      location: 'ON_SITE',
      intervalMinutes: 2.5,
      interventionType: 'DYNAMIC',
    },
    assessments: {
      baseline: { score: 52 },
      final: { score: 74 },
    },
  };

  it('renders session info correctly', () => {
    render(<SessionCard session={mockSession} />);

    expect(screen.getByText('16yo, Grade 10')).toBeInTheDocument();
    expect(screen.getByText('ON-SITE')).toBeInTheDocument();
    expect(screen.getByText('+22')).toBeInTheDocument(); // Learning gain
  });

  it('highlights active sessions', () => {
    const activeSession = { ...mockSession, status: 'IN_PROGRESS' };
    const { container } = render(<SessionCard session={activeSession} />);

    expect(container.firstChild).toHaveClass('border-green-500');
  });
});
```

**Coverage Target**: > 80% for components, > 90% for utilities

### 10.2 Integration Tests (Cypress)

**Example: Dashboard Flow**
```typescript
// cypress/e2e/dashboard.cy.ts
describe('Dashboard Overview', () => {
  beforeEach(() => {
    cy.login('researcher@university.edu', 'password123');
    cy.visit('/overview');
  });

  it('loads overview metrics', () => {
    cy.get('[data-testid="total-sessions"]').should('contain', '456');
    cy.get('[data-testid="active-sessions"]').should('be.visible');
  });

  it('navigates to condition detail', () => {
    cy.contains('On-Site × 2.5min × Dynamic').click();
    cy.url().should('include', '/conditions/');
    cy.contains('18 students completed').should('be.visible');
  });

  it('exports data', () => {
    cy.visit('/export');
    cy.get('select[name="format"]').select('csv');
    cy.get('button').contains('Generate Export').click();
    cy.contains('Export started').should('be.visible');
  });
});
```

### 10.3 E2E Tests (Playwright)

**Example: Real-Time Monitoring**
```typescript
// tests/live-monitoring.spec.ts
import { test, expect } from '@playwright/test';

test('live monitoring updates in real-time', async ({ page }) => {
  await page.goto('/live');

  // Check initial active count
  const initialCount = await page.locator('[data-testid="active-count"]').textContent();

  // Simulate new session starting (via API)
  await startMockSession();

  // Wait for WebSocket update
  await page.waitForTimeout(2000);

  // Verify count increased
  const newCount = await page.locator('[data-testid="active-count"]').textContent();
  expect(parseInt(newCount!)).toBeGreaterThan(parseInt(initialCount!));
});
```

---

## 11. Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up Amplify project & repository
- [ ] Configure Cognito user pools
- [ ] Create DynamoDB schema & tables
- [ ] Build AppSync GraphQL API (schema + basic resolvers)
- [ ] Deploy initial infrastructure (CDK)

### Phase 2: Core Dashboard (Weeks 3-5)
- [ ] React project setup (Vite + TypeScript + Tailwind)
- [ ] Authentication flow (login, logout, user management)
- [ ] Overview dashboard (metrics, recent sessions)
- [ ] Condition matrix view
- [ ] Session list with filtering

### Phase 3: Visualizations (Weeks 6-7)
- [ ] Recharts integration (bar charts, line charts, distributions)
- [ ] D3.js custom visualizations (timeline, heatmap)
- [ ] Session detail view (full Q&A transcript)
- [ ] Location map component (Leaflet/Mapbox)

### Phase 4: Real-Time Features (Week 8)
- [ ] AppSync subscriptions setup
- [ ] Live session monitoring dashboard
- [ ] Real-time map updates
- [ ] WebSocket reconnection handling

### Phase 5: Data Export (Week 9)
- [ ] Export configuration UI
- [ ] Lambda functions for data transformation
- [ ] S3 export storage
- [ ] Download link generation
- [ ] Email notifications (SES)

### Phase 6: Polish & Testing (Week 10-11)
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests (Cypress)
- [ ] E2E tests (Playwright)
- [ ] Performance optimization (lazy loading, caching)
- [ ] Accessibility audit (WCAG 2.1 AA)

### Phase 7: Deployment & Documentation (Week 12)
- [ ] Production deployment
- [ ] User documentation (how to use dashboard)
- [ ] Admin documentation (user management, troubleshooting)
- [ ] Handoff & training

**Total Timeline**: ~12 weeks (3 months)

---

## 12. File Structure

```
socratic-dashboard/
├── src/
│   ├── main.tsx                  # Entry point
│   ├── App.tsx                   # Root component
│   ├── components/
│   │   ├── auth/
│   │   │   ├── Authenticator.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── dashboard/
│   │   │   ├── OverviewDashboard.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   └── ConditionPerformanceChart.tsx
│   │   ├── conditions/
│   │   │   ├── ConditionMatrix.tsx
│   │   │   ├── ConditionCard.tsx
│   │   │   └── ConditionDetail.tsx
│   │   ├── sessions/
│   │   │   ├── SessionList.tsx
│   │   │   ├── SessionCard.tsx
│   │   │   ├── SessionDetail.tsx
│   │   │   └── SessionTimeline.tsx
│   │   ├── live/
│   │   │   ├── LiveMonitoring.tsx
│   │   │   ├── LocationMap.tsx
│   │   │   └── ActiveSessionCard.tsx
│   │   ├── export/
│   │   │   ├── DataExport.tsx
│   │   │   └── ExportHistoryTable.tsx
│   │   └── shared/
│   │       ├── Layout.tsx
│   │       ├── Sidebar.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts           # GraphQL client
│   │   │   ├── queries.ts
│   │   │   ├── mutations.ts
│   │   │   └── subscriptions.ts
│   │   ├── hooks/
│   │   │   ├── useSession.ts
│   │   │   ├── useConditions.ts
│   │   │   ├── useLiveUpdates.ts
│   │   │   └── useExport.ts
│   │   ├── store/
│   │   │   └── dashboardStore.ts   # Zustand store
│   │   └── utils/
│   │       ├── formatters.ts
│   │       ├── calculations.ts
│   │       └── validators.ts
│   ├── types/
│   │   ├── graphql.ts              # Generated types
│   │   ├── session.ts
│   │   └── condition.ts
│   └── styles/
│       └── globals.css
├── graphql/
│   ├── schema.graphql
│   └── codegen.yml                 # GraphQL Code Generator config
├── infrastructure/
│   ├── lib/
│   │   └── dashboard-stack.ts      # AWS CDK stack
│   ├── bin/
│   │   └── app.ts
│   └── cdk.json
├── cypress/
│   └── e2e/
│       ├── dashboard.cy.ts
│       └── export.cy.ts
├── tests/
│   ├── components/
│   └── e2e/
├── public/
│   └── favicon.ico
├── amplify.yml                     # Amplify build config
├── vite.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

---

## 13. API Contract Specifications

### 13.1 GraphQL Schema (Complete)

**Full schema at**: `/Users/williamprior/Development/GitHub/socratic-ai-benchmarks/graphql/schema.graphql`

(Included earlier in section 4.1)

### 13.2 REST API Alternative (if not using GraphQL)

**Base URL**: `https://api.socratic-research.com/v1`

**Authentication**: Bearer token in `Authorization` header

#### Endpoints

**Sessions**
```
GET    /sessions                    # List all sessions
GET    /sessions/:id                # Get session details
GET    /sessions/active             # List active sessions
POST   /sessions                    # Create new session (admin)
PATCH  /sessions/:id                # Update session
DELETE /sessions/:id                # Delete session (admin)
```

**Conditions**
```
GET    /conditions                  # List all conditions
GET    /conditions/:id/metrics      # Get condition metrics
```

**Students**
```
GET    /students                    # List students
GET    /students/:id                # Get student profile
GET    /students/:id/sessions       # Get student's sessions
```

**Analytics**
```
GET    /analytics/aggregate         # Aggregate metrics
GET    /analytics/conditions/:id    # Condition-specific metrics
```

**Export**
```
POST   /export                      # Request export
GET    /export/:jobId               # Check export status
GET    /export/:jobId/download      # Download export file
```

#### Response Format

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "pagination": {
      "page": 1,
      "perPage": 50,
      "total": 456,
      "pages": 10
    }
  },
  "timestamp": "2025-10-23T15:30:00Z"
}
```

#### Error Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid session ID",
    "details": { ... }
  },
  "timestamp": "2025-10-23T15:30:00Z"
}
```

---

## 14. Security Considerations

### 14.1 Authentication
- **MFA Enforcement**: Optional for researchers, required for admins
- **Password Policy**: 12+ chars, mixed case, numbers, symbols
- **Session Timeout**: 8 hours for researchers, 4 hours for admins
- **Token Refresh**: Automatic via Cognito

### 14.2 Authorization
- **Role-Based Access Control (RBAC)**:
  - Administrators: Full CRUD
  - Researchers: Read + Export
  - PIs: Read all + Delete own data
- **Field-Level Security**: Hide student PII from non-admin users
- **Row-Level Security**: Only access sessions from assigned conditions

### 14.3 Data Protection
- **Encryption at Rest**: DynamoDB encryption (AWS KMS)
- **Encryption in Transit**: TLS 1.3 for all API calls
- **PII Handling**: No student names in database (UUIDs only)
- **Data Retention**: 3-year retention policy, automated deletion
- **Audit Logging**: CloudTrail logs all data access

### 14.4 Compliance
- **FERPA**: Student data never exposed without consent
- **IRB Requirements**: Audit trails for all data access
- **GDPR-Readiness**: Right to deletion, data portability

---

## 15. Cost Estimation (Monthly)

**Assumptions**: 1000 sessions/month, 10 concurrent dashboard users

| Service | Usage | Cost |
|---------|-------|------|
| **Amplify Hosting** | Build minutes (100) + storage (5GB) | $5 |
| **Cognito** | 50 active users | Free tier |
| **AppSync** | 500k queries + 100k subscriptions | $8 |
| **DynamoDB** | 10GB storage + on-demand reads/writes | $12 |
| **Lambda** | Export jobs (100 invocations) | $1 |
| **S3** | Export storage (20GB) | $1 |
| **CloudWatch** | Logs + metrics | $5 |
| **Data Transfer** | 50GB out | $5 |
| **Total** | | **~$37/month** |

**Scaling**: Costs increase ~linearly with session volume. At 10k sessions/month: ~$150/month.

---

## Conclusion

This dashboard architecture provides:

1. **Complete Visibility**: Real-time and historical views of all 24 experimental conditions
2. **Researcher Ergonomics**: Intuitive drill-down from overview → condition → session → intervention
3. **Statistical Readiness**: Export formats designed for R/Python analysis pipelines
4. **Scalability**: Serverless architecture handles 10-10,000 sessions without re-architecture
5. **Security**: FERPA-compliant with role-based access and audit logging
6. **Maintainability**: Type-safe React + GraphQL, comprehensive testing, clear documentation

**Next Steps**:
1. Review and approve architecture
2. Confirm technology choices (GraphQL vs REST, React vs alternatives)
3. Begin Phase 1 infrastructure setup
4. Design initial wireframes with research team
5. Start parallel development of backend (CDK) and frontend (React)

**Questions for Research Team**:
1. Do you need multi-tenancy (multiple universities running studies)?
2. Should we add video playback in dashboard (review what students saw)?
3. Do you want AI-generated insights ("Condition X performs 23% better when...")?
4. What statistical tests should be pre-computed (t-tests, ANOVA, effect sizes)?
5. Should exports include raw audio transcripts of student responses?
