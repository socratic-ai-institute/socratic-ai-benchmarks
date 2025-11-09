# Test and Deploy Skill

## Description
Comprehensive testing and deployment workflow for Socratic AI Benchmarks.

## When to Use
- Before committing code
- Before deploying to AWS
- When validating changes

## Workflow

1. **Run Unit Tests**
   ```bash
   cd /home/user/socratic-ai-benchmarks
   make test-unit
   ```

2. **Check Code Formatting**
   ```bash
   make check-format
   ```

3. **Run Security Checks**
   ```bash
   make check-security
   ```

4. **Validate Configuration**
   ```bash
   make validate-config
   ```

5. **Run Full Audit (if time allows)**
   ```bash
   make audit
   ```

6. **Deploy to AWS**
   ```bash
   make deploy
   ```

## Success Criteria
- All unit tests pass
- No formatting issues
- No security vulnerabilities
- Configuration is valid
- Deployment succeeds without errors

## Common Issues

### Tests Failing
- Check if dependencies are installed: `make install-dev`
- Clear caches: `make clean`
- Review test output for specific failures

### Deployment Fails
- Verify AWS credentials are configured
- Check CDK version compatibility
- Review CloudFormation logs in AWS Console

### Configuration Invalid
- Validate JSON syntax in config files
- Ensure model_capabilities.json exists
- Check for missing required fields

## Related Commands
- `make help` - Show all available commands
- `make clean` - Clean temporary files
- `make list-models` - List configured models
