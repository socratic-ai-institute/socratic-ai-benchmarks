# Socratic Dashboard API Reference

Quick reference for all GraphQL queries, mutations, and subscriptions.

**Base URL**: `https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql`

**Authentication**: Bearer token in `Authorization` header (Cognito JWT)

---

## Table of Contents

1. [Queries](#queries)
2. [Mutations](#mutations)
3. [Subscriptions](#subscriptions)
4. [Types](#types)
5. [Examples](#examples)

---

## Queries

### List Sessions

Get paginated list of sessions with optional filtering.

```graphql
query ListSessions(
  $filter: SessionFilter
  $limit: Int = 50
  $nextToken: String
) {
  listSessions(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      sessionId
      studentId
      status
      startTime
      condition {
        location
        intervalMinutes
        interventionType
      }
      student {
        age
        grade
      }
      assessments {
        baseline { score }
        final { score }
      }
    }
    nextToken
  }
}
```

**Variables**:
```json
{
  "filter": {
    "status": "COMPLETED",
    "condition": {
      "location": "ON_SITE"
    }
  },
  "limit": 50
}
```

**Response**:
```json
{
  "data": {
    "listSessions": {
      "items": [
        {
          "sessionId": "8a3f4b2c",
          "studentId": "student-123",
          "status": "COMPLETED",
          "startTime": "2025-10-23T14:30:00Z",
          "condition": {
            "location": "ON_SITE",
            "intervalMinutes": 2.5,
            "interventionType": "DYNAMIC"
          },
          "student": {
            "age": 16,
            "grade": 10
          },
          "assessments": {
            "baseline": { "score": 52 },
            "final": { "score": 74 }
          }
        }
      ],
      "nextToken": "eyJ2ZXJzaW9uIjoy..."
    }
  }
}
```

---

### Get Session

Retrieve complete details for a single session.

```graphql
query GetSession($sessionId: ID!) {
  getSession(sessionId: $sessionId) {
    sessionId
    studentId
    status
    startTime
    endTime

    condition {
      location
      intervalMinutes
      interventionType
    }

    student {
      age
      grade
      richmondResident
    }

    locationData {
      type
      name
      verified
      verificationMethod
      coordinates
      checkInTime
    }

    contentDelivery {
      formatChosen
      totalDuration
      actualCompletionTime
      segmentsCompleted
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
      midpoint {
        score
        timeTaken
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

    postSurvey {
      locationImpact
      interventionHelpful
      wouldRecommend
      openFeedback
    }
  }
}
```

**Variables**:
```json
{
  "sessionId": "8a3f4b2c"
}
```

---

### Get Aggregate Metrics

Dashboard overview metrics.

```graphql
query AggregateMetrics($dateRange: DateRangeInput) {
  aggregateMetrics(dateRange: $dateRange) {
    totalSessions
    activeSessions
    completionRate
    averageGainOverall

    topCondition {
      location
      intervalMinutes
      interventionType
    }

    bottomCondition {
      location
      intervalMinutes
      interventionType
    }

    byLocation {
      location
      sessionCount
      averageGain
    }

    byInterval {
      intervalMinutes
      sessionCount
      averageGain
    }
  }
}
```

**Variables**:
```json
{
  "dateRange": {
    "start": "2025-10-01T00:00:00Z",
    "end": "2025-10-31T23:59:59Z"
  }
}
```

**Response**:
```json
{
  "data": {
    "aggregateMetrics": {
      "totalSessions": 456,
      "activeSessions": 23,
      "completionRate": 87.3,
      "averageGainOverall": 12.4,
      "topCondition": {
        "location": "ON_SITE",
        "intervalMinutes": 2.5,
        "interventionType": "DYNAMIC"
      },
      "bottomCondition": {
        "location": "HOME",
        "intervalMinutes": 10,
        "interventionType": "STATIC"
      },
      "byLocation": [
        { "location": "ON_SITE", "sessionCount": 120, "averageGain": 15.2 },
        { "location": "LEARNING_SPACE", "sessionCount": 98, "averageGain": 13.1 }
      ]
    }
  }
}
```

---

### Get Condition Metrics

Detailed metrics for a specific condition.

```graphql
query ConditionMetrics($condition: ConditionInput!) {
  conditionMetrics(condition: $condition) {
    condition {
      location
      intervalMinutes
      interventionType
    }

    nStudentsEnrolled
    nSessionsCompleted
    nSessionsDropped

    averageCompletionTime
    completionTimeStdDev

    dropoutRate

    comprehensionMetrics {
      baselineAvg
      baselineStdDev
      finalAvg
      finalStdDev
      gainAvg
      gainStdDev
      gainMin
      gainMax
    }

    interventionMetrics {
      averageDuration
      durationStdDev
      questionQualityAvg
      answerDepthAvg
    }

    sessions {
      sessionId
      learningGain
      completionTime
    }
  }
}
```

**Variables**:
```json
{
  "condition": {
    "location": "ON_SITE",
    "intervalMinutes": 2.5,
    "interventionType": "DYNAMIC"
  }
}
```

---

### List Active Sessions

Get all currently in-progress sessions (for live monitoring).

```graphql
query ActiveSessions {
  listSessions(filter: { status: IN_PROGRESS }) {
    items {
      sessionId
      studentId
      startTime

      student {
        age
        grade
      }

      condition {
        location
        intervalMinutes
        interventionType
      }

      locationData {
        type
        coordinates
      }

      currentSegment
      interventionProgress {
        questionNumber
        answered
        timestamp
      }
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "listSessions": {
      "items": [
        {
          "sessionId": "9f21abc",
          "studentId": "student-456",
          "startTime": "2025-10-23T15:30:00Z",
          "student": { "age": 15, "grade": 10 },
          "condition": {
            "location": "HOME",
            "intervalMinutes": 5,
            "interventionType": "STATIC"
          },
          "locationData": {
            "type": "HOME",
            "coordinates": null
          },
          "currentSegment": 2,
          "interventionProgress": {
            "questionNumber": 2,
            "answered": true,
            "timestamp": 1729698000
          }
        }
      ]
    }
  }
}
```

---

### Get Student

Retrieve student profile and all their sessions.

```graphql
query GetStudent($studentId: ID!) {
  getStudent(studentId: $studentId) {
    studentId
    age
    grade
    richmondResident

    sessions {
      sessionId
      startTime
      status
      condition {
        location
        intervalMinutes
        interventionType
      }
      assessments {
        baseline { score }
        final { score }
      }
    }

    stats {
      totalSessions
      completedSessions
      averageLearningGain
      preferredLocation
    }
  }
}
```

---

## Mutations

### Update Session

Modify session details (admin only).

```graphql
mutation UpdateSession($sessionId: ID!, $updates: SessionUpdateInput!) {
  updateSession(sessionId: $sessionId, updates: $updates) {
    sessionId
    status
    updatedAt
  }
}
```

**Variables**:
```json
{
  "sessionId": "8a3f4b2c",
  "updates": {
    "status": "COMPLETED"
  }
}
```

---

### Flag Session Anomaly

Mark session for review.

```graphql
mutation FlagAnomaly($sessionId: ID!, $reason: String!) {
  flagSessionAnomaly(sessionId: $sessionId, reason: $reason) {
    sessionId
    status
    flagged
    flagReason
    flaggedAt
    flaggedBy
  }
}
```

**Variables**:
```json
{
  "sessionId": "8a3f4b2c",
  "reason": "Suspiciously short intervention duration (5 seconds)"
}
```

**Response**:
```json
{
  "data": {
    "flagSessionAnomaly": {
      "sessionId": "8a3f4b2c",
      "status": "ANOMALY",
      "flagged": true,
      "flagReason": "Suspiciously short intervention duration (5 seconds)",
      "flaggedAt": "2025-10-23T15:45:00Z",
      "flaggedBy": "admin@university.edu"
    }
  }
}
```

---

### Request Export

Create data export job.

```graphql
mutation RequestExport($input: ExportInput!) {
  requestExport(input: $input) {
    jobId
    status
    estimatedCompletionTime
    rowCountEstimate
    fileSizeEstimate
  }
}
```

**Variables**:
```json
{
  "input": {
    "filters": {
      "dateRange": {
        "start": "2025-10-01T00:00:00Z",
        "end": "2025-10-31T23:59:59Z"
      },
      "conditions": [
        {
          "location": "ON_SITE",
          "intervalMinutes": 2.5,
          "interventionType": "DYNAMIC"
        }
      ],
      "includeIncomplete": false,
      "anonymize": true
    },
    "format": "CSV"
  }
}
```

**Response**:
```json
{
  "data": {
    "requestExport": {
      "jobId": "export-abc123",
      "status": "PENDING",
      "estimatedCompletionTime": "2025-10-23T15:50:00Z",
      "rowCountEstimate": 1234,
      "fileSizeEstimate": 2456789
    }
  }
}
```

---

### Get Export Job

Check export job status and get download URL when complete.

```graphql
query GetExportJob($jobId: ID!) {
  getExportJob(jobId: $jobId) {
    jobId
    status
    createdAt
    completedAt

    downloadUrl
    expiresAt

    fileSize
    rowCount
    format

    error
  }
}
```

**Response (completed)**:
```json
{
  "data": {
    "getExportJob": {
      "jobId": "export-abc123",
      "status": "COMPLETED",
      "createdAt": "2025-10-23T15:45:00Z",
      "completedAt": "2025-10-23T15:48:30Z",
      "downloadUrl": "https://s3.amazonaws.com/socratic-exports/export-abc123.csv?signature=...",
      "expiresAt": "2025-10-23T16:48:30Z",
      "fileSize": 2456789,
      "rowCount": 1234,
      "format": "CSV",
      "error": null
    }
  }
}
```

---

## Subscriptions

### On Session Update

Subscribe to real-time session updates.

```graphql
subscription OnSessionUpdate($sessionId: ID) {
  onSessionUpdate(sessionId: $sessionId) {
    sessionId
    status
    currentSegment

    interventionProgress {
      questionNumber
      answered
      timestamp
    }

    assessments {
      baseline { score }
      midpoint { score }
      final { score }
    }

    updatedAt
  }
}
```

**Variables (optional - filter by session)**:
```json
{
  "sessionId": "8a3f4b2c"
}
```

**Example Update Event**:
```json
{
  "data": {
    "onSessionUpdate": {
      "sessionId": "8a3f4b2c",
      "status": "IN_PROGRESS",
      "currentSegment": 3,
      "interventionProgress": {
        "questionNumber": 2,
        "answered": true,
        "timestamp": 1729698120
      },
      "assessments": {
        "baseline": { "score": 52 },
        "midpoint": { "score": 64 },
        "final": null
      },
      "updatedAt": "2025-10-23T15:42:00Z"
    }
  }
}
```

---

### On New Session

Subscribe to new session creation events.

```graphql
subscription OnNewSession {
  onNewSession {
    sessionId
    studentId
    startTime
    condition {
      location
      intervalMinutes
      interventionType
    }
    student {
      age
      grade
    }
  }
}
```

**Example Event**:
```json
{
  "data": {
    "onNewSession": {
      "sessionId": "new-session-123",
      "studentId": "student-789",
      "startTime": "2025-10-23T15:50:00Z",
      "condition": {
        "location": "CLASSROOM",
        "intervalMinutes": 5,
        "interventionType": "STATIC"
      },
      "student": {
        "age": 17,
        "grade": 11
      }
    }
  }
}
```

---

### On Condition Metrics Update

Subscribe to condition-level metric updates (recalculated every 5 minutes).

```graphql
subscription OnConditionMetricsUpdate($condition: ConditionInput) {
  onConditionMetricsUpdate(condition: $condition) {
    condition {
      location
      intervalMinutes
      interventionType
    }
    nSessionsCompleted
    averageComprehensionGain
    completionRate
    updatedAt
  }
}
```

---

## Types

### SessionStatus

```graphql
enum SessionStatus {
  SCHEDULED
  IN_PROGRESS
  COMPLETED
  DROPPED
  ANOMALY
}
```

### Location

```graphql
enum Location {
  ON_SITE
  LEARNING_SPACE
  CLASSROOM
  HOME
}
```

### InterventionType

```graphql
enum InterventionType {
  STATIC
  DYNAMIC
}
```

### ContentFormat

```graphql
enum ContentFormat {
  AUDIO
  TEXT
}
```

### ExportFormat

```graphql
enum ExportFormat {
  CSV
  JSON
  PARQUET
}
```

### ExportStatus

```graphql
enum ExportStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
}
```

---

## Examples

### Example 1: Dashboard Overview

Get all data for overview page in one request.

```graphql
query DashboardOverview {
  aggregateMetrics {
    totalSessions
    activeSessions
    completionRate
    averageGainOverall
  }

  recentSessions: listSessions(
    limit: 10
    filter: { status: COMPLETED }
  ) {
    items {
      sessionId
      student { age, grade }
      condition { location, intervalMinutes, interventionType }
      assessments {
        baseline { score }
        final { score }
      }
    }
  }

  activeSessions: listSessions(
    filter: { status: IN_PROGRESS }
  ) {
    items {
      sessionId
      currentSegment
      locationData { coordinates }
    }
  }
}
```

---

### Example 2: Condition Comparison

Compare two conditions side-by-side.

```graphql
query CompareConditions(
  $condition1: ConditionInput!
  $condition2: ConditionInput!
) {
  condition1: conditionMetrics(condition: $condition1) {
    nSessionsCompleted
    comprehensionMetrics {
      gainAvg
      gainStdDev
    }
  }

  condition2: conditionMetrics(condition: $condition2) {
    nSessionsCompleted
    comprehensionMetrics {
      gainAvg
      gainStdDev
    }
  }
}
```

**Variables**:
```json
{
  "condition1": {
    "location": "ON_SITE",
    "intervalMinutes": 2.5,
    "interventionType": "DYNAMIC"
  },
  "condition2": {
    "location": "HOME",
    "intervalMinutes": 10,
    "interventionType": "STATIC"
  }
}
```

---

### Example 3: Export All Data

Request full data export (all conditions, all time).

```graphql
mutation ExportAllData {
  requestExport(
    input: {
      filters: {
        includeIncomplete: false
        anonymize: true
      }
      format: CSV
    }
  ) {
    jobId
    estimatedCompletionTime
  }
}
```

Then poll for completion:

```graphql
query PollExport {
  getExportJob(jobId: "export-abc123") {
    status
    downloadUrl
    expiresAt
  }
}
```

---

### Example 4: Real-Time Monitoring

Subscribe to all active sessions for live map.

```typescript
// React component
import { useSubscription } from '@apollo/client';

function LiveMonitoring() {
  const { data } = useSubscription(ON_SESSION_UPDATE);

  useEffect(() => {
    if (data?.onSessionUpdate) {
      updateMapMarker(data.onSessionUpdate);
    }
  }, [data]);

  return <MapView sessions={activeSessions} />;
}
```

---

### Example 5: Search Sessions

Search sessions by student age or grade.

```graphql
query SearchSessions($ageMin: Int, $gradeMin: Int) {
  listSessions(
    filter: {
      student: {
        ageMin: $ageMin
        gradeMin: $gradeMin
      }
    }
  ) {
    items {
      sessionId
      student { age, grade }
      assessments {
        baseline { score }
        final { score }
      }
    }
  }
}
```

**Variables**:
```json
{
  "ageMin": 16,
  "gradeMin": 10
}
```

---

## Error Handling

### Error Types

**AuthenticationError** (401)
```json
{
  "errors": [
    {
      "message": "Unauthorized",
      "errorType": "UnauthorizedException",
      "errorInfo": "JWT token expired or invalid"
    }
  ]
}
```

**AuthorizationError** (403)
```json
{
  "errors": [
    {
      "message": "Access denied",
      "errorType": "UnauthorizedException",
      "errorInfo": "User not in required group: Administrators"
    }
  ]
}
```

**ValidationError** (400)
```json
{
  "errors": [
    {
      "message": "Validation error",
      "errorType": "ValidationException",
      "errorInfo": {
        "field": "sessionId",
        "message": "Invalid UUID format"
      }
    }
  ]
}
```

**NotFoundError** (404)
```json
{
  "errors": [
    {
      "message": "Session not found",
      "errorType": "ResourceNotFoundException",
      "errorInfo": {
        "sessionId": "nonexistent-id"
      }
    }
  ]
}
```

**ServerError** (500)
```json
{
  "errors": [
    {
      "message": "Internal server error",
      "errorType": "InternalServerException",
      "errorInfo": "An unexpected error occurred. Request ID: abc-123-def"
    }
  ]
}
```

---

## Rate Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Queries | 1,000 requests | per minute |
| Mutations | 100 requests | per minute |
| Subscriptions | 50 connections | per user |
| Export requests | 10 requests | per hour |

**Rate Limit Headers** (HTTP):
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1729698120
```

**Rate Limit Error**:
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded",
      "errorType": "ThrottledException",
      "errorInfo": {
        "retryAfter": 60,
        "limit": 1000,
        "window": "1 minute"
      }
    }
  ]
}
```

---

## Pagination

All list queries support cursor-based pagination:

```graphql
query PaginatedSessions($nextToken: String) {
  listSessions(limit: 50, nextToken: $nextToken) {
    items { ... }
    nextToken  # Pass this to next request
  }
}
```

**Example pagination loop** (JavaScript):
```javascript
async function getAllSessions() {
  let allSessions = [];
  let nextToken = null;

  do {
    const response = await client.query({
      query: LIST_SESSIONS,
      variables: { nextToken }
    });

    allSessions.push(...response.data.listSessions.items);
    nextToken = response.data.listSessions.nextToken;
  } while (nextToken);

  return allSessions;
}
```

---

## Testing API

### Using GraphQL Playground

1. Navigate to AppSync Console → Your API → "Queries"
2. Click "Login with Cognito"
3. Enter researcher credentials
4. Paste query from this reference
5. Click "Play" (▶)

### Using Postman

**Setup**:
1. Create new request
2. Method: POST
3. URL: `https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql`
4. Headers:
   - `Content-Type: application/json`
   - `Authorization: Bearer <JWT_TOKEN>`
5. Body (raw JSON):
```json
{
  "query": "query { aggregateMetrics { totalSessions } }"
}
```

### Using cURL

```bash
# Get aggregate metrics
curl -X POST https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "query": "query { aggregateMetrics { totalSessions activeSessions } }"
  }'
```

### Getting JWT Token

```bash
# Login via Cognito
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id your-client-id \
  --auth-parameters \
    USERNAME=researcher@university.edu,\
    PASSWORD=yourpassword

# Extract IdToken from response
export JWT_TOKEN="eyJraWQiOiJ..."
```

---

## Code Generation

Generate TypeScript types from schema:

```bash
npm run codegen
```

**Generated file** (`src/types/graphql.ts`):
```typescript
export type Session = {
  sessionId: string;
  studentId: string;
  status: SessionStatus;
  condition: Condition;
  // ... all fields
};

export type Query = {
  listSessions: (args: ListSessionsArgs) => SessionConnection;
  getSession: (args: { sessionId: string }) => Session | null;
  // ...
};

// React Query hooks
export const useListSessionsQuery = (
  variables: ListSessionsQueryVariables
) => useQuery(['listSessions', variables], ...);
```

**Usage in component**:
```tsx
import { useListSessionsQuery } from '@/types/graphql';

function SessionList() {
  const { data, loading, error } = useListSessionsQuery({
    filter: { status: 'COMPLETED' },
    limit: 50
  });

  if (loading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return <Table sessions={data.listSessions.items} />;
}
```

---

## Version History

- **v1.0.0** (2025-10-23): Initial API design
- **v1.1.0** (TBD): Add student profile queries
- **v1.2.0** (TBD): Add custom report generation
- **v2.0.0** (TBD): Multi-study support

---

## Support

**Questions?**
- Slack: #socratic-api
- Email: api-support@university.edu
- Docs: https://docs.socraticresearch.org/api

**Report Issues**:
- GitHub: https://github.com/your-org/socratic-dashboard/issues
- Tag: `api`
