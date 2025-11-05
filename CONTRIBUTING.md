# Contributing to Socratic Benchmark

Thank you for your interest in contributing to the Socratic Benchmark project!

This is a research project, and contributions are welcome in the following areas:

---

## How to Contribute

### 1. Run the CLI and Test

The best way to contribute is to **test the CLI** and report issues or suggest improvements.

**Steps**:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/socratic-ai-benchmarks.git
cd socratic-ai-benchmarks

# 2. Configure AWS + Bedrock
export AWS_REGION=us-east-1
export BEDROCK_MODEL_IDS='[
  "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "meta.llama3-1-70b-instruct-v1:0"
]'

# 3. Build the Docker image
docker build -t socratic-runner .

# 4. Run a test
docker run --rm \
  -e AWS_REGION \
  -e BEDROCK_MODEL_IDS \
  socratic-runner \
  --model anthropic.claude-3-5-sonnet-20241022-v1:0 \
  --prompt "I'm considering a career change but unsure where to start."

# 5. Report issues or suggest improvements
```

**What to look for**:
- Does the CLI work as documented?
- Are the Socratic questions high quality?
- Are error messages clear?
- Is the output format useful?

---

### 2. Propose Model List Changes

To add or remove models from the Bedrock registry:

**Steps**:

1. Open an issue with the title: **"Model Request: [Model Name]"**
2. Include:
   - Bedrock model ID (e.g., `anthropic.claude-3-5-sonnet-20241022-v1:0`)
   - Provider (e.g., Anthropic, Meta, Mistral)
   - Use case (dialogue, judge, or both)
   - Rationale (why this model should be included/excluded)

**Example issue**:

```
Title: Model Request: Claude 3.5 Haiku

**Model ID**: anthropic.claude-3-5-haiku-20241022-v1:0
**Provider**: Anthropic
**Use case**: Dialogue (high-volume runs)
**Rationale**: Fast and affordable for testing scenarios at scale.
```

**Review process**:
1. Maintainers verify model availability in Bedrock
2. Test model with CLI
3. If approved, add to `BEDROCK_MODEL_IDS` list in docs

---

### 3. Improve Documentation

Documentation improvements are always welcome!

**Areas to improve**:
- Fix typos or unclear sections
- Add examples or use cases
- Improve diagrams or explanations
- Add troubleshooting tips

**Steps**:

1. Fork the repository
2. Make changes to `README.md` or `docs/*.md`
3. Submit a pull request with:
   - Description of changes
   - Reason for improvement

**Example PR title**: "docs: Add troubleshooting for Bedrock throttling"

---

### 4. Report Bugs

If you encounter bugs or unexpected behavior:

**Steps**:

1. Open an issue with the title: **"Bug: [Brief description]"**
2. Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Docker version, AWS region)
   - Relevant logs or error messages

**Example issue**:

```
Title: Bug: CLI crashes with InvalidModelId error

**Steps to reproduce**:
1. Set BEDROCK_MODEL_IDS to ["anthropic.claude-3-5-sonnet-20241022-v1:0"]
2. Run: docker run ... --model anthropic.claude-3-sonnet-20240229-v1:0
3. CLI crashes with InvalidModelId

**Expected**: Clear error message stating model not in allowed list

**Actual**: Stack trace

**Environment**: macOS 14.0, Docker 24.0.6, us-east-1
```

---

### 5. Suggest Features

We welcome feature suggestions, especially for:
- New benchmark metrics
- Enhanced CLI options
- Better output formats
- Dashboard improvements

**Steps**:

1. Open an issue with the title: **"Feature Request: [Brief description]"**
2. Include:
   - Use case (why this feature is needed)
   - Proposed solution (how it should work)
   - Alternatives considered

**Example issue**:

```
Title: Feature Request: Export results to CSV

**Use case**: Researchers want to analyze results in spreadsheets

**Proposed solution**: Add `--format csv` flag to CLI

**Alternatives**: Export to JSON and use external tools to convert
```

---

## Code of Conduct

### Expected Behavior

- Be respectful and inclusive
- Provide constructive feedback
- Focus on facts and problem-solving
- Respect project scope (Phase 1 focus)

### Unacceptable Behavior

- Harassment or discriminatory language
- Spam or off-topic comments
- Demanding features outside project scope

---

## Development Workflow (For Maintainers)

### Local Development

```bash
# 1. Clone and install dependencies
git clone https://github.com/your-org/socratic-ai-benchmarks.git
cd socratic-ai-benchmarks
pip install -r requirements.txt

# 2. Run tests
pytest tests/

# 3. Validate docs
make docs

# 4. Build Docker image
docker build -t socratic-runner .

# 5. Test CLI
docker run --rm -e AWS_REGION -e BEDROCK_MODEL_IDS socratic-runner \
  --model anthropic.claude-3-5-sonnet-20241022-v1:0 \
  --prompt "Test prompt"
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and commit: `git commit -m "feat: Add feature X"`
4. Push to your fork: `git push origin feature/my-feature`
5. Open a pull request with:
   - Clear description
   - Linked issue (if applicable)
   - Test results

**Commit message format** (recommended):

```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation only
- refactor: Code refactor
- test: Add tests
- chore: Maintenance
```

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (TBD pending publication).

---

## Questions?

If you have questions about contributing:

1. Check the [README.md](README.md) and [docs/](docs/) first
2. Search existing issues
3. Open a new issue with the "Question" label

---

## Acknowledgments

Thank you for helping improve the Socratic Benchmark project!

---

*Last Updated: 2025-11-05*
