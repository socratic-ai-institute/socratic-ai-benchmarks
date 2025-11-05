# Makefile for Socratic Benchmark Documentation

.PHONY: help docs docs-check docs-links docs-anchors docs-serve clean

# Default target
help:
	@echo "Socratic Benchmark - Documentation Targets"
	@echo ""
	@echo "Available targets:"
	@echo "  make docs         - Validate all documentation (links + anchors)"
	@echo "  make docs-check   - Check if all doc files exist"
	@echo "  make docs-links   - Validate markdown links"
	@echo "  make docs-anchors - Validate anchor links"
	@echo "  make docs-serve   - Serve docs locally (future)"
	@echo "  make clean        - Clean temporary files"
	@echo ""

# Validate all documentation
docs: docs-check docs-links docs-anchors
	@echo "✅ All documentation checks passed!"

# Check if all expected doc files exist
docs-check:
	@echo "Checking documentation files..."
	@test -f README.md || (echo "❌ Missing: README.md" && exit 1)
	@test -f CHANGELOG.md || (echo "❌ Missing: CHANGELOG.md" && exit 1)
	@test -f CONTRIBUTING.md || (echo "❌ Missing: CONTRIBUTING.md" && exit 1)
	@test -f docs/architecture.md || (echo "❌ Missing: docs/architecture.md" && exit 1)
	@test -f docs/runner.md || (echo "❌ Missing: docs/runner.md" && exit 1)
	@test -f docs/bedrock.md || (echo "❌ Missing: docs/bedrock.md" && exit 1)
	@test -f docs/benchmark.md || (echo "❌ Missing: docs/benchmark.md" && exit 1)
	@echo "✅ All expected doc files exist"

# Validate markdown links (internal and external)
docs-links:
	@echo "Validating markdown links..."
	@command -v markdown-link-check >/dev/null 2>&1 || \
		(echo "⚠️  markdown-link-check not installed. Install with: npm install -g markdown-link-check" && exit 0)
	@find . -name "*.md" \
		-not -path "./archive/*" \
		-not -path "./phase1-model-selection/*" \
		-not -path "./phase2-research-experiment/*" \
		-not -path "./serverless/*" \
		-not -path "./.git/*" \
		-not -path "./node_modules/*" \
		-exec markdown-link-check {} \;
	@echo "✅ All markdown links validated"

# Validate anchor links (internal references like #heading)
docs-anchors:
	@echo "Validating anchor links..."
	@echo "Checking README.md..."
	@grep -o '\[.*\](#[^)]*)' README.md | sed 's/.*(\(#[^)]*\))/\1/' | while read anchor; do \
		if ! grep -q "^##.*" README.md | grep -q "$$(echo $$anchor | tr '[:upper:]' '[:lower:]' | sed 's/#//')"; then \
			echo "⚠️  Potentially broken anchor in README.md: $$anchor"; \
		fi; \
	done
	@echo "Checking docs/*.md..."
	@for file in docs/*.md; do \
		echo "  Checking $$file..."; \
		grep -o '\[.*\](#[^)]*)' $$file 2>/dev/null | sed 's/.*(\(#[^)]*\))/\1/' | while read anchor; do \
			if ! grep -q "^##.*" $$file | grep -q "$$(echo $$anchor | tr '[:upper:]' '[:lower:]' | sed 's/#//')"; then \
				echo "⚠️  Potentially broken anchor in $$file: $$anchor"; \
			fi; \
		done; \
	done
	@echo "✅ Anchor link validation complete"

# Serve docs locally (for future use with mkdocs or similar)
docs-serve:
	@echo "Local docs server not yet implemented."
	@echo "Consider using: python -m http.server 8000"
	@echo "Then visit: http://localhost:8000"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleaned temporary files"

# Build Docker image (convenience target)
docker-build:
	@echo "Building Docker image..."
	docker build -t socratic-runner .
	@echo "✅ Docker image built: socratic-runner"

# Run Docker CLI test (convenience target)
docker-test:
	@echo "Running Docker CLI test..."
	@test -n "$$AWS_REGION" || (echo "❌ AWS_REGION not set" && exit 1)
	@test -n "$$BEDROCK_MODEL_IDS" || (echo "❌ BEDROCK_MODEL_IDS not set" && exit 1)
	docker run --rm \
		-e AWS_REGION \
		-e BEDROCK_MODEL_IDS \
		socratic-runner \
		--model anthropic.claude-3-5-sonnet-20241022-v1:0 \
		--prompt "I'm considering a career change but unsure where to start." \
		--turns 3
	@echo "✅ Docker CLI test complete"
