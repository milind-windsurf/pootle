#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone test script for docker image validation functionality.
This can be used to test the validation logic independently of Django.
"""

import subprocess
import json
import sys

def validate_image(image):
    """Validate a single Docker image"""
    result = {
        'image': image,
        'exists': False,
        'accessible': False,
        'size': None,
        'created': None,
        'error': None
    }
    
    try:
        inspect_cmd = ['docker', 'inspect', image]
        inspect_result = subprocess.Popen(
            inspect_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        stdout, stderr = inspect_result.communicate()
        
        if inspect_result.returncode == 0:
            result['exists'] = True
            result['accessible'] = True
            
            inspect_data = json.loads(stdout)
            if inspect_data:
                image_data = inspect_data[0]
                result['size'] = image_data.get('Size')
                result['created'] = image_data.get('Created')
        else:
            print("Image {0} not found locally, attempting to pull...".format(image))
            pull_cmd = ['docker', 'pull', image]
            pull_result = subprocess.Popen(
                pull_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            pull_stdout, pull_stderr = pull_result.communicate()
            
            if pull_result.returncode == 0:
                result['exists'] = True
                result['accessible'] = True
                inspect_result2 = subprocess.Popen(inspect_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout2, stderr2 = inspect_result2.communicate()
                if inspect_result2.returncode == 0:
                    inspect_data = json.loads(stdout2)
                    if inspect_data:
                        image_data = inspect_data[0]
                        result['size'] = image_data.get('Size')
                        result['created'] = image_data.get('Created')
            else:
                result['error'] = pull_stderr.strip()
                
    except ValueError:
        result['error'] = 'Invalid JSON response from docker inspect'
    except Exception as e:
        result['error'] = str(e)
        
    return result

def format_size(size_bytes):
    """Format size in bytes to human readable format"""
    if not size_bytes:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return "{0:.1f}{1}".format(size_bytes, unit)
        size_bytes /= 1024.0
    return "{0:.1f}TB".format(size_bytes)

def main():
    """Main function to test docker image validation"""
    if len(sys.argv) < 2:
        print("Usage: python test_docker_validation.py <image1> [image2] ...")
        print("   or: python test_docker_validation.py --file <filename>")
        sys.exit(1)
    
    images = []
    if sys.argv[1] == '--file':
        if len(sys.argv) < 3:
            print("Error: --file option requires a filename")
            sys.exit(1)
        try:
            with open(sys.argv[2], 'r') as f:
                images = [line.strip() for line in f if line.strip()]
        except IOError as e:
            print("Error reading file: {0}".format(e))
            sys.exit(1)
    else:
        images = sys.argv[1:]
    
    print("Validating {0} Docker images...".format(len(images)))
    print("=" * 100)
    print("{0:<40} {1:<15} {2:<15} {3:<20}".format('Image', 'Status', 'Size', 'Created'))
    print("=" * 100)
    
    results = []
    for image in images:
        print("Validating {0}...".format(image))
        result = validate_image(image)
        results.append(result)
        
        status = "[OK] Valid" if result['accessible'] else "[FAIL] Invalid"
        size = format_size(result['size']) if result['size'] else "N/A"
        created = result['created'][:19] if result['created'] else "N/A"
        
        print("{0:<40} {1:<15} {2:<15} {3:<20}".format(result['image'], status, size, created))
        
        if result['error']:
            print("  Error: {0}".format(result['error']))
    
    print("=" * 100)
    valid_count = sum(1 for r in results if r['accessible'])
    print("Summary: {0}/{1} images are valid and accessible".format(valid_count, len(results)))
    
    return results

if __name__ == '__main__':
    main()
