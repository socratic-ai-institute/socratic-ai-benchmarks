# Archive

This directory contains superseded implementations and future design documents that are not part of the current MVP.

## Contents

### `infrastructure-typescript/`
**Status**: ⚠️ Superseded
**Reason**: Duplicate CDK implementation in TypeScript
**Superseded by**: `serverless/infra/` (Python CDK)

This was an early TypeScript CDK implementation that overlapped with the serverless Python CDK. We chose Python for consistency with Lambda handlers and the Phase 1 evaluation framework.

**Do not deploy this stack.** Use `serverless/infra/` instead.

---

### `lambdas-old/`
**Status**: ⚠️ Superseded
**Reason**: Incomplete lambda stubs
**Superseded by**: `serverless/lambdas/` (complete implementation)

These were early lambda function stubs (planner, dialogue, shared utils) that were never fully implemented. The complete working lambdas are in `serverless/lambdas/` with:
- planner/
- runner/
- judge/
- curator/
- api/

**Do not reference these stubs.** Use `serverless/lambdas/` instead.

---

### `phase3-batch-architecture/`
**Status**: 📋 Future Design
**Reason**: Production architecture for Phase 3 (research experiment)
**Current alternative**: `serverless/` (Lambda-based MVP for Phase 2)

This directory contains **design documents only** (no implementation) for a production-grade architecture using:
- AWS Batch / Fargate (for long-running jobs)
- Step Functions (complex orchestration)
- Athena + QuickSight (advanced analytics)
- ~$33/week cost (vs. ~$2/week for Lambda MVP)

**When to use**: Phase 3 (research experiment with 120-240 students)
**Current phase**: Phase 2 (serverless benchmarking MVP)

This represents a **different architectural approach** than the Phase 2 MVP:

| Aspect | Phase 2 (serverless/) | Phase 3 (this archive) |
|--------|----------------------|------------------------|
| **Compute** | Lambda (15 min max) | Batch/Fargate (unlimited) |
| **Orchestration** | SQS queues | Step Functions |
| **Scale** | 60 turns/week | 7,200 turns/week |
| **Cost** | ~$2/week | ~$33/week |
| **Status** | ✅ Deployed | 📋 Design only |

**Keep for**: Future reference when scaling to Phase 3

---

## Why Archive?

**Problem**: Multiple overlapping implementations caused confusion about which code to deploy.

**Solution**: Consolidate on **single source of truth** for MVP:
- **Phase 1**: `phase1-model-selection/` (CLI-based evaluation)
- **Phase 2**: `serverless/` (Lambda-based weekly benchmarking)
- **Phase 3**: TBD (will reference designs from `phase3-batch-architecture/`)

**Result**: Clear path forward with archived designs preserved for future use.

---

## How to Reference Archived Content

### If you need the TypeScript CDK:
**Don't.** Use `serverless/infra/` (Python CDK) instead. It's complete and tested.

### If you need lambda code:
**Don't use these stubs.** Use `serverless/lambdas/` which has:
- Complete implementations (5 functions)
- Shared library layer (`serverless/lib/`)
- Working event sources and integrations

### If you're planning Phase 3:
**Do reference** `phase3-batch-architecture/` for:
- Step Functions orchestration patterns
- Batch job definitions
- Advanced analytics with Athena/QuickSight
- Cost modeling for production scale

---

## Restoring Archived Content

If you need to restore any of these implementations:

```bash
# View what was archived
git log --all --full-history -- "archive/*"

# Restore specific directory (if needed)
git checkout <commit> -- archive/infrastructure-typescript
git mv archive/infrastructure-typescript infrastructure
```

**Warning**: Only restore if you have a specific reason. The current `serverless/` implementation is the tested, working MVP.

---

## Questions?

See [`VISION.md`](../VISION.md) for the complete phased roadmap and decision rationale.
