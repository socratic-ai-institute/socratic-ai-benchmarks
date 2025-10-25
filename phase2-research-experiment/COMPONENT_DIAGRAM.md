# Socratic Dashboard Component & Data Flow Diagrams

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          RESEARCHER DASHBOARD (Browser)                      │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         React Application (SPA)                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │   Overview   │  │  Conditions  │  │   Sessions   │  [More pages]  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  │                                                                         │  │
│  │  State Management:                                                     │  │
│  │  • React Query (Server state) • Zustand (UI state)                    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                   ↕                                          │
│                    Authentication Layer (Cognito)                            │
│                                   ↕                                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕
                       GraphQL API (AWS AppSync)
                                    ↕
┌──────────────────────────────────────────────────────────────────────────────┐
│                            AWS BACKEND SERVICES                              │
│                                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │   DynamoDB     │  │    Lambda      │  │      S3        │                │
│  │  (Sessions,    │  │  (Business     │  │  (Exports)     │                │
│  │   Students,    │  │   Logic,       │  │                │                │
│  │   Conditions)  │  │   Analytics)   │  │                │                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
│                                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │   Cognito      │  │  CloudWatch    │  │   EventBridge  │                │
│  │  (Auth, Users, │  │  (Logs,        │  │  (Scheduled    │                │
│  │   Groups)      │  │   Metrics)     │  │   Jobs)        │                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕
┌──────────────────────────────────────────────────────────────────────────────┐
│                        STUDENT APPLICATION (Mobile/Web)                      │
│  • Completes learning sessions                                               │
│  • Generates intervention data                                               │
│  • Sends updates to backend                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 2. Frontend Component Hierarchy

```
<App>
│
├── <Authenticator>
│   └── [Cognito Login UI]
│
└── <AuthenticatedApp>
    │
    ├── <Layout>
    │   ├── <Header>
    │   │   ├── <Logo>
    │   │   ├── <Navigation>
    │   │   └── <UserMenu>
    │   │
    │   ├── <Sidebar>
    │   │   ├── <NavLink> (Overview)
    │   │   ├── <NavLink> (Conditions)
    │   │   ├── <NavLink> (Sessions)
    │   │   ├── <NavLink> (Live)
    │   │   ├── <NavLink> (Export)
    │   │   └── <FilterPanel>
    │   │       ├── <DateRangePicker>
    │   │       ├── <LocationFilter>
    │   │       └── <IntervalFilter>
    │   │
    │   └── <MainContent>
    │       └── <Router>
    │           │
    │           ├── Route: /overview
    │           │   └── <OverviewDashboard>
    │           │       ├── <MetricCard> (Total Sessions)
    │           │       ├── <MetricCard> (Active Sessions)
    │           │       ├── <MetricCard> (Completion Rate)
    │           │       ├── <MetricCard> (Avg Learning Gain)
    │           │       ├── <ConditionPerformanceChart>
    │           │       │   └── [Recharts BarChart]
    │           │       ├── <RecentSessionsTable>
    │           │       │   └── <SessionRow> (repeated)
    │           │       └── <LocationHeatmap>
    │           │           └── [D3.js Visualization]
    │           │
    │           ├── Route: /conditions
    │           │   └── <ConditionMatrix>
    │           │       └── <ConditionGroup> (per location)
    │           │           └── <ConditionCard> (6 per location)
    │           │               ├── <ConditionLabel>
    │           │               ├── <StudentCount>
    │           │               ├── <LearningGainBadge>
    │           │               └── <ProgressBar>
    │           │
    │           ├── Route: /conditions/:id
    │           │   └── <ConditionDetail>
    │           │       ├── <ConditionHeader>
    │           │       ├── <ConditionMetrics>
    │           │       │   ├── <MetricCard> (N Students)
    │           │       │   ├── <MetricCard> (Avg Gain)
    │           │       │   └── <MetricCard> (Completion Rate)
    │           │       ├── <ScoreDistributionChart>
    │           │       │   └── [Recharts Histogram]
    │           │       ├── <InterventionDurationChart>
    │           │       │   └── [Recharts BoxPlot]
    │           │       └── <SessionsInConditionTable>
    │           │           └── <SessionRow> (repeated)
    │           │
    │           ├── Route: /sessions
    │           │   └── <SessionList>
    │           │       ├── <SessionFilters>
    │           │       │   ├── <StatusFilter>
    │           │       │   ├── <ConditionFilter>
    │           │       │   └── <SearchInput>
    │           │       └── <VirtualizedSessionTable>
    │           │           └── <SessionRow> (virtualized)
    │           │               ├── <SessionID>
    │           │               ├── <StudentInfo>
    │           │               ├── <ConditionBadge>
    │           │               ├── <StatusBadge>
    │           │               └── <ScoreSummary>
    │           │
    │           ├── Route: /sessions/:id
    │           │   └── <SessionDetail>
    │           │       ├── <SessionHeader>
    │           │       │   ├── <BackButton>
    │           │       │   ├── <SessionMetadata>
    │           │       │   └── <ExportButton>
    │           │       ├── <SessionTimeline>
    │           │       │   └── [D3.js Custom Viz]
    │           │       ├── <ScoreCards>
    │           │       │   ├── <MetricCard> (Baseline)
    │           │       │   ├── <MetricCard> (Final)
    │           │       │   └── <MetricCard> (Gain)
    │           │       ├── <InterventionsSection>
    │           │       │   └── <Accordion>
    │           │       │       └── <InterventionPanel> (repeated)
    │           │       │           ├── <InterventionHeader>
    │           │       │           └── <QASequence>
    │           │       │               └── <QAPair> (repeated)
    │           │       │                   ├── <Question>
    │           │       │                   ├── <Answer>
    │           │       │                   └── <QualityMetrics>
    │           │       ├── <AssessmentsSection>
    │           │       │   └── <AssessmentCard> (repeated)
    │           │       │       └── <ResponseList>
    │           │       └── <LocationVerification>
    │           │           ├── <LocationDetails>
    │           │           └── <MiniMap>
    │           │               └── [Leaflet Map]
    │           │
    │           ├── Route: /live
    │           │   └── <LiveMonitoring>
    │           │       ├── <MapView>
    │           │       │   └── <MapContainer>
    │           │       │       ├── <TileLayer>
    │           │       │       └── <LocationMarker> (repeated)
    │           │       │           └── <Popup>
    │           │       ├── <ActiveSessionsList>
    │           │       │   └── <ActiveSessionCard> (repeated)
    │           │       │       ├── <StudentInfo>
    │           │       │       ├── <ProgressBar>
    │           │       │       └── <LiveIndicator>
    │           │       └── <SessionProgressPanel>
    │           │           ├── <SegmentProgress>
    │           │           └── <InterventionStatus>
    │           │
    │           └── Route: /export
    │               └── <DataExport>
    │                   ├── <ExportConfiguration>
    │                   │   ├── <DateRangePicker>
    │                   │   ├── <ConditionMultiSelect>
    │                   │   ├── <OptionsCheckboxes>
    │                   │   ├── <FormatSelector>
    │                   │   ├── <EstimationPreview>
    │                   │   └── <GenerateButton>
    │                   └── <ExportHistory>
    │                       └── <ExportHistoryTable>
    │                           └── <ExportRow> (repeated)
    │                               ├── <ExportStatus>
    │                               ├── <ExportMetadata>
    │                               └── <DownloadButton>
    │
    └── <ErrorBoundary>
        └── <ErrorFallback>
```

## 3. Data Flow Patterns

### 3.1 Query Flow (Read Operations)

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER INTERACTION                                                    │
│  User clicks "Overview" tab                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  REACT COMPONENT                                                     │
│  <OverviewDashboard> renders                                         │
│                                                                       │
│  useQuery({                                                          │
│    queryKey: ['aggregateMetrics'],                                   │
│    queryFn: fetchAggregateMetrics                                    │
│  })                                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  REACT QUERY                                                         │
│  1. Check cache for ['aggregateMetrics']                             │
│  2. If stale or missing, execute fetchAggregateMetrics()            │
│  3. Set loading state                                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  API CLIENT                                                          │
│  GraphQL query via AWS Amplify:                                      │
│                                                                       │
│  query AggregateMetrics {                                            │
│    aggregateMetrics {                                                │
│      totalSessions                                                   │
│      activeSessions                                                  │
│      completionRate                                                  │
│      averageGainOverall                                              │
│    }                                                                 │
│  }                                                                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  AWS APPSYNC                                                         │
│  1. Validates JWT token (Cognito)                                    │
│  2. Routes to resolver                                               │
│  3. Invokes Lambda function                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  LAMBDA RESOLVER                                                     │
│  aggregateMetricsResolver()                                          │
│  1. Query DynamoDB (Sessions table)                                  │
│  2. Aggregate data (count, avg, etc.)                                │
│  3. Return formatted result                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  DYNAMODB                                                            │
│  Table: Sessions                                                     │
│  Query: Scan with filters                                            │
│  Returns: Array of session records                                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
        [Response flows back up the chain]
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  REACT QUERY                                                         │
│  1. Store result in cache                                            │
│  2. Set data state                                                   │
│  3. Trigger component re-render                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  COMPONENT UPDATE                                                    │
│  <OverviewDashboard> re-renders with metrics data                    │
│  • <MetricCard> shows totalSessions                                  │
│  • <MetricCard> shows activeSessions                                 │
│  • Charts update with new data                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Mutation Flow (Write Operations)

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER INTERACTION                                                    │
│  User flags session as anomaly                                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  REACT COMPONENT                                                     │
│  <SessionDetail> button click                                        │
│                                                                       │
│  const mutation = useMutation({                                      │
│    mutationFn: (sessionId) =>                                        │
│      flagSessionAnomaly(sessionId, "Suspicious timing")              │
│  })                                                                  │
│                                                                       │
│  mutation.mutate(sessionId)                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  OPTIMISTIC UPDATE (React Query)                                     │
│  1. Cancel outgoing queries for this session                         │
│  2. Snapshot current data                                            │
│  3. Update cache optimistically (show "ANOMALY" status immediately)  │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  API CLIENT                                                          │
│  GraphQL mutation:                                                   │
│                                                                       │
│  mutation FlagAnomaly($id: ID!, $reason: String!) {                 │
│    flagSessionAnomaly(sessionId: $id, reason: $reason) {            │
│      sessionId                                                       │
│      status                                                          │
│      flaggedAt                                                       │
│    }                                                                 │
│  }                                                                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  AWS APPSYNC                                                         │
│  1. Validates JWT + checks user group (Administrators only)          │
│  2. Invokes mutation resolver                                        │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  LAMBDA RESOLVER                                                     │
│  flagSessionAnomalyResolver()                                        │
│  1. Update DynamoDB (set status = ANOMALY)                           │
│  2. Log to CloudWatch (audit trail)                                  │
│  3. Send notification (SNS → Email)                                  │
│  4. Return updated session                                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  DYNAMODB                                                            │
│  Table: Sessions                                                     │
│  UpdateItem: sessionId                                               │
│  Set: status = "ANOMALY", flaggedAt = timestamp                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
        [Response flows back]
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  REACT QUERY (onSuccess)                                             │
│  1. Confirm optimistic update                                        │
│  2. Invalidate related queries (['session', sessionId])              │
│  3. Show success toast                                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  COMPONENT UPDATE                                                    │
│  • Badge updates to "ANOMALY"                                        │
│  • Toast notification: "Session flagged successfully"                │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Real-Time Subscription Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  COMPONENT MOUNT                                                     │
│  <LiveMonitoring> component renders                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  SUBSCRIBE TO UPDATES                                                │
│  useSubscription({                                                   │
│    subscription: gql`                                                │
│      subscription OnSessionUpdate {                                  │
│        onSessionUpdate {                                             │
│          sessionId                                                   │
│          currentSegment                                              │
│          interventionProgress { ... }                                │
│        }                                                             │
│      }                                                               │
│    `                                                                 │
│  })                                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  AWS APPSYNC                                                         │
│  1. Establish WebSocket connection                                   │
│  2. Register subscription                                            │
│  3. Keep connection alive                                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
        [WebSocket connection maintained]
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STUDENT APP (separate system)                                       │
│  Student completes Segment 2                                         │
│  → POST /sessions/:id/progress                                       │
│     { currentSegment: 2 }                                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  API GATEWAY / APPSYNC MUTATION                                      │
│  updateSessionProgress() mutation                                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  LAMBDA RESOLVER                                                     │
│  1. Update DynamoDB (Sessions table)                                 │
│  2. Return updated session                                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  DYNAMODB STREAM                                                     │
│  Captures change event (currentSegment: 1 → 2)                       │
│  Triggers Lambda function                                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  BROADCAST LAMBDA                                                    │
│  broadcastSessionUpdate()                                            │
│  1. Read change from DynamoDB Stream                                 │
│  2. Publish to AppSync subscription                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  AWS APPSYNC                                                         │
│  Pushes update to all subscribed clients via WebSocket              │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  DASHBOARD (subscribed client)                                       │
│  useSubscription receives update                                     │
│                                                                       │
│  onData: (data) => {                                                │
│    // Update local state                                             │
│    setActiveSessions(prev =>                                         │
│      updateSession(prev, data.onSessionUpdate)                       │
│    )                                                                 │
│  }                                                                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  COMPONENT UPDATE                                                    │
│  <LiveMonitoring> re-renders                                         │
│  • Map marker updates position (if GPS changed)                      │
│  • Progress bar animates to 50% (segment 2 of 4)                     │
│  • Session card highlights (brief flash animation)                   │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. State Management Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           APPLICATION STATE                          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ↓                                 ↓
┌──────────────────────────────┐  ┌──────────────────────────────┐
│      SERVER STATE            │  │       CLIENT STATE           │
│    (React Query)             │  │       (Zustand)              │
├──────────────────────────────┤  ├──────────────────────────────┤
│                              │  │                              │
│ Queries:                     │  │ UI State:                    │
│ • aggregateMetrics           │  │ • selectedConditions         │
│ • sessions                   │  │ • dateRange                  │
│ • conditions                 │  │ • sidebarOpen                │
│ • students                   │  │ • activeTab                  │
│                              │  │                              │
│ Mutations:                   │  │ View Preferences:            │
│ • updateSession              │  │ • theme (light/dark)         │
│ • flagAnomaly                │  │ • chartType (bar/line)       │
│ • requestExport              │  │ • tablePageSize              │
│                              │  │                              │
│ Subscriptions:               │  │ Filters:                     │
│ • onSessionUpdate            │  │ • statusFilter               │
│ • onNewSession               │  │ • locationFilter             │
│                              │  │ • searchQuery                │
│ Cache:                       │  │                              │
│ • 5min stale time            │  │ Persistence:                 │
│ • 10min garbage collection   │  │ • localStorage               │
│ • Automatic refetch          │  │ • Session storage            │
└──────────────────────────────┘  └──────────────────────────────┘
```

### 4.1 React Query Cache Structure

```javascript
// Cache Key Structure
{
  "['aggregateMetrics']": {
    data: { totalSessions: 456, activeSessions: 23, ... },
    dataUpdatedAt: 1729698000000,
    isStale: false
  },

  "['sessions', { status: 'COMPLETED', limit: 50 }]": {
    data: { items: [...], nextToken: "..." },
    dataUpdatedAt: 1729698000000,
    isStale: false
  },

  "['session', '8a3f4b2c']": {
    data: { sessionId: '8a3f4b2c', student: {...}, ... },
    dataUpdatedAt: 1729698000000,
    isStale: false
  },

  "['conditions']": {
    data: [{ location: 'ON_SITE', ... }, ...],
    dataUpdatedAt: 1729698000000,
    isStale: true // Needs refetch
  }
}
```

### 4.2 Zustand Store Structure

```typescript
interface DashboardStore {
  // UI State
  sidebarOpen: boolean;
  activeTab: string;
  theme: 'light' | 'dark';

  // Filters
  filters: {
    dateRange: { start: Date | null; end: Date | null };
    locations: Location[];
    intervals: number[];
    status: SessionStatus[];
    searchQuery: string;
  };

  // View Preferences
  preferences: {
    chartType: 'bar' | 'line' | 'scatter';
    tablePageSize: 25 | 50 | 100;
    mapZoom: number;
    showHeatmap: boolean;
  };

  // Actions
  setSidebarOpen: (open: boolean) => void;
  setActiveTab: (tab: string) => void;
  updateFilters: (filters: Partial<Filters>) => void;
  updatePreferences: (prefs: Partial<Preferences>) => void;
  resetFilters: () => void;
}
```

## 5. API Request/Response Flows

### 5.1 List Sessions (Paginated)

**Request:**
```graphql
query ListSessions($limit: Int, $nextToken: String) {
  listSessions(
    filter: { status: COMPLETED }
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      sessionId
      studentId
      condition {
        location
        intervalMinutes
        interventionType
      }
      status
      startTime
      assessments {
        baseline { score }
        final { score }
      }
    }
    nextToken
  }
}
```

**Response:**
```json
{
  "data": {
    "listSessions": {
      "items": [
        {
          "sessionId": "8a3f4b2c",
          "studentId": "student-123",
          "condition": {
            "location": "ON_SITE",
            "intervalMinutes": 2.5,
            "interventionType": "DYNAMIC"
          },
          "status": "COMPLETED",
          "startTime": "2025-10-23T14:30:00Z",
          "assessments": {
            "baseline": { "score": 52 },
            "final": { "score": 74 }
          }
        }
        // ... more items
      ],
      "nextToken": "eyJ2ZXJzaW9uIjoy..."
    }
  }
}
```

### 5.2 Get Session Detail

**Request:**
```graphql
query GetSession($id: ID!) {
  getSession(sessionId: $id) {
    sessionId
    studentId
    condition {
      location
      intervalMinutes
      interventionType
    }
    locationData {
      type
      name
      verified
      verificationMethod
      coordinates
    }
    student {
      age
      grade
      richmondResident
    }
    interventions {
      timestamp
      type
      questions
      answers
      durationSeconds
      questionQualityScores
      answerDepthScores
    }
    assessments {
      baseline {
        score
        timeTaken
        responses {
          questionId
          answer
          correct
        }
      }
      final {
        score
        timeTaken
        responses {
          questionId
          answer
          correct
        }
      }
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "getSession": {
      "sessionId": "8a3f4b2c",
      "studentId": "student-123",
      "condition": { ... },
      "locationData": {
        "type": "ON_SITE",
        "name": "Tredegar Iron Works",
        "verified": true,
        "verificationMethod": "GPS",
        "coordinates": [37.5316, -77.4481]
      },
      "student": {
        "age": 16,
        "grade": 10,
        "richmondResident": true
      },
      "interventions": [
        {
          "timestamp": 150,
          "type": "DYNAMIC",
          "questions": [
            "What stood out to you about the founding of Tredegar?",
            "Building on your observation, how do you think...",
            "Connecting these ideas, what role did..."
          ],
          "answers": [
            "I thought it was interesting that...",
            "Well, I think the location near the river...",
            "The James River provided both power and..."
          ],
          "durationSeconds": 95,
          "questionQualityScores": [3.8, 4.1, 4.3],
          "answerDepthScores": [2.1, 3.2, 3.8]
        }
        // ... more interventions
      ],
      "assessments": { ... }
    }
  }
}
```

### 5.3 Request Data Export

**Request:**
```graphql
mutation RequestExport($input: ExportInput!) {
  requestExport(input: $input) {
    jobId
    status
    estimatedCompletionTime
  }
}

# Variables:
{
  "input": {
    "filters": {
      "dateRange": {
        "start": "2025-10-01T00:00:00Z",
        "end": "2025-10-31T23:59:59Z"
      },
      "conditions": ["ON_SITE_2.5_DYNAMIC", "HOME_5.0_STATIC"],
      "includeIncomplete": false,
      "anonymize": true
    },
    "format": "CSV"
  }
}
```

**Response:**
```json
{
  "data": {
    "requestExport": {
      "jobId": "export-abc123",
      "status": "PENDING",
      "estimatedCompletionTime": "2025-10-23T15:05:00Z"
    }
  }
}
```

**Poll Export Status:**
```graphql
query GetExportJob($jobId: ID!) {
  getExportJob(jobId: $jobId) {
    jobId
    status
    downloadUrl
    expiresAt
    fileSize
    rowCount
  }
}
```

**Response (when complete):**
```json
{
  "data": {
    "getExportJob": {
      "jobId": "export-abc123",
      "status": "COMPLETED",
      "downloadUrl": "https://s3.amazonaws.com/exports/export-abc123.csv?signature=...",
      "expiresAt": "2025-10-23T16:00:00Z",
      "fileSize": 2456789,
      "rowCount": 1234
    }
  }
}
```

## 6. Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  API CALL                                                            │
│  fetchSessions()                                                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
                        [Network Request]
                                 ↓
                    ┌────────────┴────────────┐
                    │                         │
                    ↓                         ↓
        ┌──────────────────┐      ┌──────────────────┐
        │   SUCCESS        │      │    ERROR         │
        └────────┬─────────┘      └────────┬─────────┘
                 │                         │
                 ↓                         ↓
    ┌──────────────────────┐  ┌──────────────────────────────────┐
    │ React Query          │  │ Error Type Analysis              │
    │ • Store in cache     │  ├──────────────────────────────────┤
    │ • Update component   │  │ Network Error?                   │
    └──────────────────────┘  │ • Show retry button              │
                              │ • Log to CloudWatch              │
                              │                                  │
                              │ Authentication Error (401)?      │
                              │ • Clear token                    │
                              │ • Redirect to login              │
                              │                                  │
                              │ Authorization Error (403)?       │
                              │ • Show "Access Denied" message   │
                              │ • Suggest contact admin          │
                              │                                  │
                              │ Validation Error (400)?          │
                              │ • Show field-specific errors     │
                              │ • Highlight invalid inputs       │
                              │                                  │
                              │ Server Error (500)?              │
                              │ • Show generic error message     │
                              │ • Auto-retry (3x with backoff)   │
                              │ • Alert monitoring system        │
                              └──────────────────────────────────┘
                                             ↓
                              ┌──────────────────────────────────┐
                              │ Error Boundary (React)           │
                              │ • Catch render errors            │
                              │ • Show fallback UI               │
                              │ • Log error details              │
                              │ • Offer "Go Home" button         │
                              └──────────────────────────────────┘
```

## 7. Performance Optimization Strategies

### 7.1 Code Splitting Points

```
Entry Point (main.tsx)
  ↓
App Shell (Layout, Auth) [Eager Load]
  ↓
┌───────────────────────────────────────────────────────────┐
│                 Route-Based Splitting                     │
├───────────────────────────────────────────────────────────┤
│ /overview      → OverviewDashboard.lazy.tsx   (100 KB)   │
│ /conditions    → ConditionMatrix.lazy.tsx     (80 KB)    │
│ /sessions      → SessionList.lazy.tsx         (75 KB)    │
│ /sessions/:id  → SessionDetail.lazy.tsx       (120 KB)   │
│ /live          → LiveMonitoring.lazy.tsx      (150 KB)   │
│ /export        → DataExport.lazy.tsx          (60 KB)    │
└───────────────────────────────────────────────────────────┘
  ↓
Component-Level Splitting
  • D3 Visualizations (loaded on demand)
  • Heavy charts (loaded when visible)
  • Export history (loaded on tab switch)
```

### 7.2 Data Fetching Optimization

```
┌─────────────────────────────────────────────────────────────┐
│  PARALLEL QUERIES (when independent)                        │
├─────────────────────────────────────────────────────────────┤
│  useQueries([                                               │
│    { queryKey: ['aggregateMetrics'], ... },                 │
│    { queryKey: ['recentSessions'], ... },                   │
│    { queryKey: ['conditions'], ... }                        │
│  ])                                                         │
│  → All 3 requests fire simultaneously                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  DEPENDENT QUERIES (when sequential)                        │
├─────────────────────────────────────────────────────────────┤
│  const { data: session } = useQuery(['session', id])        │
│  const { data: student } = useQuery(                        │
│    ['student', session?.studentId],                         │
│    { enabled: !!session }  ← Wait for session first        │
│  )                                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PAGINATION (for large lists)                               │
├─────────────────────────────────────────────────────────────┤
│  useInfiniteQuery({                                         │
│    queryKey: ['sessions'],                                  │
│    queryFn: ({ pageParam }) =>                              │
│      fetchSessions({ nextToken: pageParam }),               │
│    getNextPageParam: (lastPage) => lastPage.nextToken       │
│  })                                                         │
│  → Load more on scroll (infinite scroll)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PREFETCHING (anticipate user actions)                      │
├─────────────────────────────────────────────────────────────┤
│  onMouseEnter={() =>                                        │
│    queryClient.prefetchQuery({                              │
│      queryKey: ['session', sessionId],                      │
│      queryFn: () => fetchSession(sessionId)                 │
│    })                                                       │
│  }                                                          │
│  → Prefetch on hover (feels instant)                        │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Rendering Optimization

```
┌─────────────────────────────────────────────────────────────┐
│  VIRTUALIZATION (large lists)                               │
├─────────────────────────────────────────────────────────────┤
│  <VirtualizedList                                           │
│    items={1000}                                             │
│    renderCount={20}  ← Only render visible items           │
│  />                                                         │
│  → Handles 10,000+ items smoothly                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  MEMOIZATION (expensive calculations)                       │
├─────────────────────────────────────────────────────────────┤
│  const learningGains = useMemo(() =>                        │
│    sessions.map(s =>                                        │
│      s.assessments.final.score -                            │
│      s.assessments.baseline.score                           │
│    ),                                                       │
│    [sessions]  ← Only recalculate when sessions change     │
│  )                                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  COMPONENT MEMOIZATION (prevent re-renders)                 │
├─────────────────────────────────────────────────────────────┤
│  const SessionCard = memo(({ session }) => {                │
│    // Expensive render                                      │
│  }, (prev, next) =>                                         │
│    prev.session.sessionId === next.session.sessionId        │
│  )                                                          │
│  → Only re-render if sessionId changes                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

This component architecture provides:

1. **Clear Hierarchy**: Nested component structure from App → Layout → Pages → Components
2. **Data Flow Patterns**: Query, Mutation, Subscription, and Error flows fully documented
3. **State Management**: Separation of server state (React Query) and client state (Zustand)
4. **Performance**: Code splitting, lazy loading, virtualization, memoization strategies
5. **API Contracts**: Complete request/response examples for all major operations

The architecture is designed for:
- **Maintainability**: Clear component boundaries and responsibilities
- **Performance**: Optimized data fetching and rendering
- **Scalability**: Handles 10k+ sessions without performance degradation
- **Developer Experience**: Type-safe with TypeScript, intuitive patterns

Next steps: Review diagrams, approve architecture, begin implementation starting with infrastructure (Phase 1).
