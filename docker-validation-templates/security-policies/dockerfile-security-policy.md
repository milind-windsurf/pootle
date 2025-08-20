# Dockerfile Security Policy

## Overview
This document outlines security requirements and best practices for Dockerfile creation across all repositories.

## Security Requirements

### 1. Base Image Security
```dockerfile
# ✅ REQUIRED: Use specific version tags, never 'latest'
FROM python:3.9.16-slim-bullseye

# ❌ FORBIDDEN: Using latest or mutable tags
FROM python:latest
FROM ubuntu:focal
```

### 2. User Security
```dockerfile
# ✅ REQUIRED: Create and use non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# ❌ FORBIDDEN: Running as root
USER root
# or omitting USER directive entirely
```

### 3. Package Management
```dockerfile
# ✅ REQUIRED: Update packages and clean cache
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        package1 \
        package2 && \
    rm -rf /var/lib/apt/lists/*

# ❌ FORBIDDEN: Not cleaning package cache
RUN apt-get update && apt-get install -y package1
```

### 4. File Permissions
```dockerfile
# ✅ REQUIRED: Set proper file ownership
COPY --chown=appuser:appuser . /app

# ✅ REQUIRED: Set appropriate file permissions
RUN chmod 755 /app/entrypoint.sh && \
    chmod 644 /app/config.yml
```

### 5. Port Exposure
```dockerfile
# ✅ REQUIRED: Only expose necessary ports
EXPOSE 8080

# ❌ FORBIDDEN: Exposing unnecessary or dangerous ports
EXPOSE 22    # SSH
EXPOSE 3389  # RDP
EXPOSE 23    # Telnet
```

### 6. Health Checks
```dockerfile
# ✅ REQUIRED: Include health check for services
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

### 7. Environment Variables
```dockerfile
# ✅ REQUIRED: Use build args for sensitive data
ARG DATABASE_URL
ENV DATABASE_URL=${DATABASE_URL}

# ❌ FORBIDDEN: Hardcoding secrets
ENV DATABASE_PASSWORD=mysecretpassword
ENV API_KEY=abc123xyz
```

### 8. Multi-stage Builds
```dockerfile
# ✅ RECOMMENDED: Use multi-stage builds for security isolation
FROM node:16-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:16-alpine AS runtime
COPY --from=builder /app/node_modules ./node_modules
COPY . .
USER node
CMD ["node", "server.js"]
```

## Repository-Specific Requirements

### Analytics/ETL Repositories
```dockerfile
# Data processing security
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Validate data processing libraries
RUN python -c "import pandas, numpy, sqlalchemy; print('ETL dependencies verified')"

# Set resource limits
ENV MEMORY_LIMIT=2G
ENV CPU_LIMIT=2
```

### ML Model Repositories
```dockerfile
# ML framework security
RUN pip install --no-cache-dir tensorflow==2.8.0 torch==1.12.0

# Model file security
COPY --chown=appuser:appuser models/ /app/models/
RUN chmod 644 /app/models/*.pkl

# GPU compatibility check
RUN python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### Ad-Serving Repositories
```dockerfile
# Performance optimization
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    redis-tools && \
    rm -rf /var/lib/apt/lists/*

# Security headers
COPY nginx.conf /etc/nginx/nginx.conf
RUN nginx -t
```

## Automated Validation

### Hadolint Rules
```yaml
# .hadolint.yaml
ignored:
  - DL3008  # Pin versions in apt get install (handled by base image)
  
failure-threshold: error

override:
  error:
    - DL3002  # Last USER should not be root
    - DL3025  # Use arguments JSON notation for CMD and ENTRYPOINT
  warning:
    - DL3009  # Delete the apt-get lists after installing something
    - DL3015  # Avoid additional packages by specifying --no-install-recommends
```

### Security Scanning Integration
```yaml
# GitHub Actions security scan
- name: Run Hadolint
  uses: hadolint/hadolint-action@v3.1.0
  with:
    dockerfile: Dockerfile
    failure-threshold: error

- name: Run Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE_NAME }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

## Compliance Checklist

### Before Dockerfile Commit
- [ ] Base image uses specific version tag
- [ ] Non-root user is created and used
- [ ] Packages are updated and cache is cleaned
- [ ] Only necessary ports are exposed
- [ ] Health check is included (for services)
- [ ] No secrets are hardcoded
- [ ] File permissions are properly set
- [ ] Multi-stage build is used (when applicable)

### Security Review
- [ ] Dockerfile passes Hadolint validation
- [ ] Image passes vulnerability scanning
- [ ] No high/critical vulnerabilities present
- [ ] Image size is optimized
- [ ] Runtime security policies are enforced

## Violation Reporting

### Automatic Enforcement
- CI/CD pipelines will fail if security policies are violated
- Pull requests will be blocked until issues are resolved
- Security scan results will be uploaded to GitHub Security tab

### Manual Review Process
1. Security team reviews Dockerfile changes
2. Violations are documented and tracked
3. Remediation guidance is provided
4. Follow-up scans verify fixes

## Resources

### Tools
- **Hadolint**: Dockerfile linter
- **Trivy**: Vulnerability scanner
- **Snyk**: Security platform
- **Docker Bench**: Security audit tool

### Documentation
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [NIST Container Security Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)

---
*Last updated: August 20, 2025*
*Policy version: 1.0*
