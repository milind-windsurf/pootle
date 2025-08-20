# Docker Image Validation System

This tool provides comprehensive validation for Docker images, including existence checks, format validation, and basic security analysis.

## Usage

### Command Line Interface

```bash
python docker_image_validator.py !docker-image-validation <image1> [image2] [image3] ...
```

### Examples

Validate a single image:
```bash
python docker_image_validator.py !docker-image-validation caspian/sophia
```

Validate multiple images:
```bash
python docker_image_validator.py !docker-image-validation \
    caspian/sophia \
    cauldron/adaptive/adaptive-experiment \
    cauldron/amphawa-sdk \
    cauldron/base_rc \
    cauldron/conduit \
    cauldron/conduit-no-tf \
    cauldron/curated \
    cauldron/curated/rstudio \
    cauldron/dl-pytorch \
    cauldron/dl-tensorflow
```

## Validation Types

### 1. Format Validation
- Validates Docker image name format
- Checks for proper registry/namespace/repository structure
- Validates tag format

### 2. Existence Validation
- Checks if the image exists in the registry
- Uses `docker manifest inspect` to verify without downloading
- Extracts architecture information

### 3. Security Validation
- Warns about use of `latest` tag
- Checks for suspicious patterns in image names
- Provides security recommendations

## Output Format

The tool provides detailed results including:
- Overall summary with pass/fail/warning/error counts
- Per-image validation results
- Detailed information for each validation type
- Recommendations for improvements

## Exit Codes

- `0`: All validations passed
- `1`: One or more validations failed or errored
- `2`: All validations passed but with warnings

## Requirements

- Docker installed and accessible via command line
- Python 2.7+ or Python 3.x
- Network access to Docker registries

## Integration

This tool can be integrated into CI/CD pipelines, deployment scripts, or used as a standalone validation utility.

### Example Integration

```bash
#!/bin/bash
# Validate images before deployment
python tools/docker_image_validator.py !docker-image-validation \
    myapp:v1.2.3 \
    nginx:1.21-alpine \
    postgres:13

if [ $? -eq 0 ]; then
    echo "All images validated successfully"
    # Proceed with deployment
else
    echo "Image validation failed"
    exit 1
fi
```

## Extending the Validator

The validator is designed to be extensible. You can add new validation types by:

1. Adding new methods to the `DockerImageValidator` class
2. Updating the `validate_all` method to include new validations
3. Adding appropriate formatting in the `format_results` function

## Troubleshooting

### Common Issues

1. **Docker not found**: Ensure Docker is installed and in your PATH
2. **Permission denied**: Make sure your user has permission to run Docker commands
3. **Network timeouts**: Check your network connection and Docker registry accessibility
4. **Rate limiting**: Some registries may rate limit manifest requests

### Debug Mode

For debugging, you can modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG)
```
