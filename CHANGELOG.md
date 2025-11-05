# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-11-05

### Phase 1 Documentation Refactor — Bedrock-Only Routing

**Summary**: Complete documentation refactor to reflect Phase 1 scope: Socratic Disposition Benchmark (SDB) only, Bedrock-only routing, single Docker runner.

### Added

- **docs/architecture.md**: Comprehensive serverless architecture documentation
  - High-level Mermaid and ASCII diagrams
  - Data layer summary (DynamoDB + S3)
  - Services layer (all Lambda)
  - Bedrock routing section with API details
  - Cost breakdown and monitoring guidance

- **docs/runner.md**: Docker CLI contract and usage guide
  - CLI arguments (`--model`, `--prompt`, `--turns`)
  - Environment variables (AWS_REGION, BEDROCK_MODEL_IDS, etc.)
  - Output artifacts to S3 and console JSON summary
  - Sample runs and expected outputs
  - Troubleshooting section

- **docs/bedrock.md**: Bedrock routing and model configuration
  - Model registry (7 supported models)
  - How to add/remove models
  - IAM policy snippets
  - Retry/backoff strategy
  - Region guidance and throttling notes
  - Cost estimation

- **docs/benchmark.md**: Socratic Disposition Benchmark (SDB) definition
  - Complete 0–10 rubric (form, substance, purity)
  - Aggregate metrics (overall score, compliance rate, half-life)
  - Violation rates
  - S3/DynamoDB storage paths
  - Weekly rollup schema
  - Optional Athena/QuickSight integration

- **CONTRIBUTING.md**: Minimal contribution guide
  - How to run CLI tests
  - How to propose model list changes
  - Code of conduct placeholder

- **Makefile**: Docs validation targets
  - `make docs`: Validate links/anchors
  - `make docs-serve`: Local preview (future)

### Changed

- **README.md**: Complete refactor for Phase 1
  - New intro emphasizing Bedrock-only routing
  - Quickstart with Docker CLI
  - Weekly serverless flow diagram
  - Configuration table (environment variables)
  - Example Bedrock model IDs
  - Updated architecture and benchmark details
  - Simplified repository structure
  - Roadmap section for future phases

### Removed

- Stale references to direct provider SDKs (OpenAI, Anthropic, Google)
- Multi-container setup references
- Phase 2/3 detailed plans (moved to "Roadmap" summary)

### Technical Details

- All documentation now explicitly states: **"All requests go through Amazon Bedrock"**
- No direct provider SDKs are mentioned or used
- Single Docker image for CLI (Phase 1 scope)
- Lambda-based serverless architecture for weekly runs
- DynamoDB (on-demand) + S3 (raw + curated) for storage
- EventBridge → Lambda fan-out → SQS → Lambdas → DynamoDB/S3

### Migration Notes

- No code changes required (documentation only)
- Existing `phase1-model-selection/` directory marked as "legacy (pre-refactor)" in README
- Serverless implementation in `serverless/` directory unchanged

---

## [1.0.0] - 2025-10-25

### Initial Release

**Summary**: AWS Socratic Benchmark System — Complete production-grade serverless architecture.

### Added

- Complete serverless implementation (`serverless/` directory)
  - Planner, Runner, Judge, Curator, API Lambdas
  - Shared `socratic_bench` library
  - AWS CDK infrastructure (Python)
  - SQS fan-out for parallel execution
  - DynamoDB single-table design
  - S3 two-tier storage (raw + curated)
  - Static UI (vanilla JS)

- Data layer schema (DynamoDB + S3)
  - Single-table design with GSIs
  - Manifest-based idempotent runs
  - Turn-by-turn storage
  - Weekly aggregation

- Weekly automated benchmarking
  - EventBridge cron trigger (Monday 3 AM UTC)
  - Parallel dialogue execution
  - LLM-as-judge scoring
  - Result curation and materialization

- Phase 1 model selection framework
  - 8 Bedrock models tested
  - Scenario generation
  - Benchmark comparison script
  - Dashboard generation

- Documentation
  - `SERVERLESS_IMPLEMENTATION.md`: Implementation summary
  - `PROJECT_STATUS.md`: Project tracking
  - Phase 1 and Phase 2 READMEs
  - Deployment guides

### Technical Details

- **Cost**: ~$2/week (~$8/month) for weekly runs
- **Idle cost**: ~$0.35/month (DynamoDB + S3 storage only)
- **Concurrency**: Max 25 Runner + 25 Judge Lambdas
- **Storage**: DynamoDB on-demand + S3 with lifecycle policies

---

## [0.9.0] - 2025-10-20

### Pre-Release — Repository Organization

### Added

- Repository structure (Phase 1 / Phase 2 separation)
- Archive directory for outdated docs
- Basic AWS credentials configuration

### Changed

- Reorganized documentation hierarchy
- Simplified navigation

---

*For detailed implementation history, see git commit log.*

---

## Future Releases (Planned)

### [1.2.0] - TBD
- Docker image CI/CD pipeline
- Automated testing framework
- Enhanced monitoring dashboards

### [2.0.0] - TBD
- Advanced CSD (Content-Specific Dimensions) scoring
- Secondary judge validation
- AWS Batch integration for larger runs
- Multi-region support
- Enhanced UI with authentication

---

*Last Updated: 2025-11-05*
