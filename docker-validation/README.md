# Docker Image Validation Framework

A comprehensive validation framework for Docker images, designed to ensure image quality, security, and functionality across multiple data science and machine learning services.

## Overview

This framework validates Docker images across three key dimensions:
- **Build Validation**: Image pull, configuration analysis, layer optimization
- **Security Scanning**: Vulnerability detection using Trivy and Docker Scout
- **Functionality Testing**: Basic container startup and health checks

## Supported Images

The framework currently validates the following Docker images:

### Economics Data Science (econs-ds)
- `econs-ds/econs-ds-saver-dd` - Data saver service
- `econs-ds/econs-ds-spark3` - Apache Spark 3 environment
- `econs-ds/econs-ds-user-profiling` - User profiling service
- `econs-ds/mpc-spatial-temporal-surge` - Multi-party computation for spatial-temporal analysis
- `econs-ds/network-value-individual-surge` - Network value analysis
- `econs-ds/transport-dax-bounding` - Transport DAX bounding service
- `econs-ds/transport-fallback-surge` - Transport fallback surge analysis
- `econs-ds/transport-surge-geohash-config` - Transport surge geohash configuration

### Machine Learning Engineering (ff-mle)
- `ff-mle/rhps` - RHPS machine learning service
- `ff-mle/rhps-analysis` - RHPS analysis service

## Quick Start

### Prerequisites

- Python 3.9+
- Docker
- Trivy (for security scanning)
- Docker Scout (optional, for additional security scanning)

### Installation

1. Install Python dependencies:
```bash
pip install pyyaml asyncio
```

2. Install Trivy:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

### Usage

#### Validate All Images
```bash
cd docker-validation
python scripts/validate_image.py --config config/images.yaml
```

#### Validate Specific Image Group
```bash
# Validate only econs-ds images
python scripts/validate_image.py --config config/images.yaml --filter econs-ds

# Validate only ff-mle images
python scripts/validate_image.py --config config/images.yaml --filter ff-mle
```

#### Generate Report
```bash
python scripts/validate_image.py \
  --config config/images.yaml \
  --output validation-report.json \
  --verbose
```

## Configuration

### Image Configuration (`config/images.yaml`)

```yaml
images:
  - name: "econs-ds/econs-ds-saver-dd"
    registry: "docker.io"
    validation_type: ["build", "security", "functionality"]
    description: "Data saver service for economics data science"
    tags: ["latest"]

validation_config:
  timeout_seconds: 300
  parallel_jobs: 3
  security_scan_tools: ["trivy", "docker-scout"]
  build_platforms: ["linux/amd64", "linux/arm64"]
  health_check_timeout: 60
```

### Validation Types

- **build**: Validates image pull, configuration, layers, and size
- **security**: Scans for vulnerabilities and security best practices
- **functionality**: Tests basic container startup and health

## CI/CD Integration

### GitHub Actions

The framework includes a GitHub Actions workflow (`workflows/docker-validation.yml`) that:

- Runs validation on push and pull requests
- Uses matrix strategy for parallel validation
- Generates detailed reports
- Uploads artifacts for review
- Provides summary statistics

### Manual CI Setup

Copy the workflow file to your repository's `.github/workflows/` directory:

```bash
cp docker-validation/workflows/docker-validation.yml .github/workflows/
```

## Validation Results

### Report Structure

```json
{
  "validation_summary": {
    "total_images": 10,
    "passed": 8,
    "failed": 2,
    "timestamp": 1692547200
  },
  "detailed_results": [
    {
      "image": "econs-ds/econs-ds-saver-dd",
      "registry": "docker.io",
      "overall_status": "PASS",
      "validation_results": {
        "latest": {
          "build": {
            "status": "PASS",
            "tests": {...}
          },
          "security": {
            "status": "PASS",
            "scans": {...}
          },
          "functionality": {
            "status": "PASS",
            "stdout": "Container started successfully"
          }
        }
      }
    }
  ]
}
```

### Status Codes

- **PASS**: Validation successful
- **FAIL**: Validation failed
- **SKIP**: Validation skipped (e.g., tool not available)
- **PENDING**: Validation in progress

## Security Scanning

### Trivy Integration

The framework uses Trivy to scan for:
- Known vulnerabilities (CVEs)
- Security misconfigurations
- License compliance issues

### Docker Scout Integration

When available, Docker Scout provides:
- Additional vulnerability detection
- Supply chain security analysis
- Policy compliance checking

### Security Best Practices Checked

- Non-root user execution
- No exposed SSH ports
- No hardcoded secrets in environment variables
- Minimal attack surface

## Build Validation

### Image Analysis

- Architecture and OS compatibility
- Layer optimization analysis
- Size recommendations
- Configuration security review

### Optimization Recommendations

- Multi-stage build suggestions
- Large layer identification
- Size optimization tips

## Troubleshooting

### Common Issues

1. **Image Pull Failures**
   - Check network connectivity
   - Verify image name and registry
   - Ensure proper authentication

2. **Security Scan Failures**
   - Install required scanning tools
   - Check tool versions and compatibility
   - Verify image accessibility

3. **Timeout Issues**
   - Increase timeout values in configuration
   - Check system resources
   - Reduce parallel job count

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
python scripts/validate_image.py --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add new validation types or improve existing ones
4. Update documentation
5. Submit a pull request

### Adding New Images

1. Update `config/images.yaml` with new image definitions
2. Test validation with the new images
3. Update documentation

### Adding New Validation Types

1. Implement validation logic in appropriate module
2. Update configuration schema
3. Add tests and documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review troubleshooting guide
