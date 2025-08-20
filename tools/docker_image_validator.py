#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Docker Image Validation System

This module provides functionality to validate Docker images for existence,
security, and compliance. It handles the "!docker-image-validation" command
and validates specified Docker images.
"""

import sys
import subprocess
import json
import re
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DockerImageValidator:
    """Validates Docker images for various criteria."""
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_results = {}
        
    def validate_image_exists(self, image_name):
        """
        Check if a Docker image exists in the registry.
        
        Args:
            image_name (str): Name of the Docker image to validate
            
        Returns:
            dict: Validation result with status and details
        """
        try:
            cmd = ['docker', 'manifest', 'inspect', image_name]
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                manifest_data = json.loads(stdout)
                return {
                    'status': 'PASS',
                    'message': 'Image {0} exists'.format(image_name),
                    'details': {
                        'manifest_size': len(stdout),
                        'architecture': self._extract_architecture(manifest_data)
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'message': 'Image {0} not found'.format(image_name),
                    'details': {
                        'error': stderr.strip()
                    }
                }
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': 'Error validating image {0}'.format(image_name),
                'details': {'error': str(e)}
            }
    
    def validate_image_format(self, image_name):
        """
        Validate Docker image name format.
        
        Args:
            image_name (str): Name of the Docker image to validate
            
        Returns:
            dict: Validation result with status and details
        """
        pattern = r'^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?::[0-9]+)?/)?[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*(?::[a-zA-Z0-9][a-zA-Z0-9._-]*)?$'
        
        if re.match(pattern, image_name):
            return {
                'status': 'PASS',
                'message': 'Image name {0} has valid format'.format(image_name),
                'details': {
                    'registry': self._extract_registry(image_name),
                    'repository': self._extract_repository(image_name),
                    'tag': self._extract_tag(image_name)
                }
            }
        else:
            return {
                'status': 'FAIL',
                'message': 'Image name {0} has invalid format'.format(image_name),
                'details': {
                    'expected_format': '[registry/]namespace/repository[:tag]'
                }
            }
    
    def validate_image_security(self, image_name):
        """
        Perform basic security validation on Docker image.
        
        Args:
            image_name (str): Name of the Docker image to validate
            
        Returns:
            dict: Validation result with status and details
        """
        try:
            if image_name.endswith(':latest') or ':' not in image_name:
                return {
                    'status': 'WARNING',
                    'message': 'Image {0} uses latest tag'.format(image_name),
                    'details': {
                        'recommendation': 'Use specific version tags for better security and reproducibility'
                    }
                }
            
            suspicious_patterns = ['test', 'debug', 'temp', 'experimental']
            for pattern in suspicious_patterns:
                if pattern in image_name.lower():
                    return {
                        'status': 'WARNING',
                        'message': 'Image {0} contains suspicious pattern: {1}'.format(image_name, pattern),
                        'details': {
                            'pattern': pattern,
                            'recommendation': 'Verify this is a production-ready image'
                        }
                    }
            
            return {
                'status': 'PASS',
                'message': 'Image {0} passes basic security checks'.format(image_name),
                'details': {}
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': 'Error performing security validation on {0}'.format(image_name),
                'details': {'error': str(e)}
            }
    
    def validate_all(self, image_names):
        """
        Validate multiple Docker images with all validation types.
        
        Args:
            image_names (list): List of Docker image names to validate
            
        Returns:
            dict: Complete validation results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_images': len(image_names),
            'images': {}
        }
        
        for image_name in image_names:
            logger.info("Validating image: {0}".format(image_name))
            
            image_results = {
                'format_validation': self.validate_image_format(image_name),
                'existence_validation': self.validate_image_exists(image_name),
                'security_validation': self.validate_image_security(image_name)
            }
            
            statuses = [result['status'] for result in image_results.values()]
            if 'ERROR' in statuses:
                overall_status = 'ERROR'
            elif 'FAIL' in statuses:
                overall_status = 'FAIL'
            elif 'WARNING' in statuses:
                overall_status = 'WARNING'
            else:
                overall_status = 'PASS'
            
            image_results['overall_status'] = overall_status
            results['images'][image_name] = image_results
        
        overall_statuses = [img['overall_status'] for img in results['images'].values()]
        results['summary'] = {
            'passed': overall_statuses.count('PASS'),
            'failed': overall_statuses.count('FAIL'),
            'warnings': overall_statuses.count('WARNING'),
            'errors': overall_statuses.count('ERROR')
        }
        
        return results
    
    def _extract_architecture(self, manifest_data):
        """Extract architecture information from manifest data."""
        try:
            if 'manifests' in manifest_data:
                archs = [m.get('platform', {}).get('architecture', 'unknown') 
                        for m in manifest_data['manifests']]
                return list(set(archs))
            return ['unknown']
        except:
            return ['unknown']
    
    def _extract_registry(self, image_name):
        """Extract registry from image name."""
        if '/' in image_name and '.' in image_name.split('/')[0]:
            return image_name.split('/')[0]
        return 'docker.io'
    
    def _extract_repository(self, image_name):
        """Extract repository from image name."""
        parts = image_name.split(':')[0].split('/')
        if len(parts) > 1 and '.' in parts[0]:
            return '/'.join(parts[1:])
        return '/'.join(parts)
    
    def _extract_tag(self, image_name):
        """Extract tag from image name."""
        if ':' in image_name:
            return image_name.split(':')[-1]
        return 'latest'


class CommandProcessor:
    """Processes Docker image validation commands."""
    
    def __init__(self):
        """Initialize the command processor."""
        self.validator = DockerImageValidator()
    
    def process_command(self, command, args):
        """
        Process a validation command.
        
        Args:
            command (str): The command to process
            args (list): Command arguments
            
        Returns:
            dict: Command execution results
        """
        if command == '!docker-image-validation':
            return self._handle_docker_validation(args)
        else:
            return {
                'status': 'ERROR',
                'message': 'Unknown command: {0}'.format(command),
                'details': {}
            }
    
    def _handle_docker_validation(self, image_names):
        """Handle Docker image validation command."""
        if not image_names:
            return {
                'status': 'ERROR',
                'message': 'No image names provided for validation',
                'details': {}
            }
        
        return self.validator.validate_all(image_names)


def format_results(results):
    """
    Format validation results for display.
    
    Args:
        results (dict): Validation results
        
    Returns:
        str: Formatted results string
    """
    output = []
    output.append("=" * 80)
    output.append("DOCKER IMAGE VALIDATION RESULTS")
    output.append("=" * 80)
    output.append("Timestamp: {0}".format(results['timestamp']))
    output.append("Total Images: {0}".format(results['total_images']))
    output.append("")
    
    summary = results['summary']
    output.append("SUMMARY:")
    output.append("  ✓ Passed: {0}".format(summary['passed']))
    output.append("  ✗ Failed: {0}".format(summary['failed']))
    output.append("  ⚠ Warnings: {0}".format(summary['warnings']))
    output.append("  ❌ Errors: {0}".format(summary['errors']))
    output.append("")
    
    output.append("DETAILED RESULTS:")
    output.append("-" * 80)
    
    for image_name, image_results in results['images'].items():
        status_icon = {
            'PASS': '✓',
            'FAIL': '✗',
            'WARNING': '⚠',
            'ERROR': '❌'
        }.get(image_results['overall_status'], '?')
        
        output.append("{0} {1} - {2}".format(status_icon, image_name, image_results['overall_status']))
        
        for validation_type, result in image_results.items():
            if validation_type == 'overall_status':
                continue
                
            validation_name = validation_type.replace('_', ' ').title()
            status_icon = {
                'PASS': '  ✓',
                'FAIL': '  ✗',
                'WARNING': '  ⚠',
                'ERROR': '  ❌'
            }.get(result['status'], '  ?')
            
            output.append("  {0} {1}: {2}".format(status_icon, validation_name, result['message']))
            
            if result['details']:
                for key, value in result['details'].items():
                    output.append("    {0}: {1}".format(key, value))
        
        output.append("")
    
    return "\n".join(output)


def main():
    """Main entry point for the Docker image validator."""
    if len(sys.argv) < 2:
        print("Usage: python docker_image_validator.py <command> [image_names...]")
        print("Commands:")
        print("  !docker-image-validation <image1> [image2] [image3] ...")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    processor = CommandProcessor()
    results = processor.process_command(command, args)
    
    if 'images' in results:
        formatted_output = format_results(results)
        print(formatted_output)
        
        summary = results['summary']
        if summary['errors'] > 0 or summary['failed'] > 0:
            sys.exit(1)
        elif summary['warnings'] > 0:
            sys.exit(2)
        else:
            sys.exit(0)
    else:
        print("Error: {0}".format(results['message']))
        sys.exit(1)


if __name__ == '__main__':
    main()
