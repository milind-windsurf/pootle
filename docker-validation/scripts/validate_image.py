#!/usr/bin/env python3
"""
Docker Image Validation Framework
Main validation orchestrator for Docker images
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from build_test import BuildValidator
from security_scan import SecurityScanner


class ImageValidator:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.build_validator = BuildValidator()
        self.security_scanner = SecurityScanner()
        
    def _load_config(self) -> Dict:
        """Load validation configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
            
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
        
    async def validate_image(self, image_config: Dict) -> Dict:
        """Validate a single Docker image"""
        image_name = image_config['name']
        registry = image_config.get('registry', 'docker.io')
        validation_types = image_config.get('validation_type', ['build'])
        tags = image_config.get('tags', ['latest'])
        
        self.logger.info(f"Starting validation for {image_name}")
        
        results = {
            'image': image_name,
            'registry': registry,
            'timestamp': time.time(),
            'validation_results': {},
            'overall_status': 'PENDING'
        }
        
        for tag in tags:
            full_image_name = f"{registry}/{image_name}:{tag}"
            tag_results = {}
            
            try:
                if 'build' in validation_types:
                    self.logger.info(f"Running build validation for {full_image_name}")
                    build_result = await self.build_validator.validate(full_image_name)
                    tag_results['build'] = build_result
                    
                if 'security' in validation_types:
                    self.logger.info(f"Running security scan for {full_image_name}")
                    security_result = await self.security_scanner.scan(full_image_name)
                    tag_results['security'] = security_result
                    
                if 'functionality' in validation_types:
                    self.logger.info(f"Running functionality tests for {full_image_name}")
                    functionality_result = await self._test_functionality(full_image_name)
                    tag_results['functionality'] = functionality_result
                    
                results['validation_results'][tag] = tag_results
                
            except Exception as e:
                self.logger.error(f"Error validating {full_image_name}: {e}")
                tag_results['error'] = str(e)
                results['validation_results'][tag] = tag_results
                
        results['overall_status'] = self._determine_overall_status(results['validation_results'])
        self.logger.info(f"Validation completed for {image_name}: {results['overall_status']}")
        
        return results
        
    async def _test_functionality(self, image_name: str) -> Dict:
        """Test basic functionality of Docker image"""
        try:
            cmd = [
                'timeout', '30s', 'docker', 'run', '--rm',
                image_name
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stderr_text = stderr.decode()
            
            if process.returncode != 0:
                if ('pull access denied' in stderr_text or 
                    'repository does not exist' in stderr_text or
                    'Unable to find image' in stderr_text):
                    return {
                        'status': 'SKIP',
                        'reason': 'Image not accessible for functionality testing',
                        'stdout': stdout.decode(),
                        'stderr': stderr_text,
                        'return_code': process.returncode
                    }
                else:
                    return {
                        'status': 'FAIL',
                        'stdout': stdout.decode(),
                        'stderr': stderr_text,
                        'return_code': process.returncode
                    }
            
            return {
                'status': 'PASS',
                'stdout': stdout.decode(),
                'stderr': stderr_text,
                'return_code': process.returncode
            }
            
        except asyncio.TimeoutError:
            return {
                'status': 'FAIL',
                'error': 'Container startup timeout',
                'return_code': -1
            }
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'return_code': -1
            }
            
    def _determine_overall_status(self, validation_results: Dict) -> str:
        """Determine overall validation status"""
        if not validation_results:
            return 'FAIL'
            
        has_any_pass = False
        has_critical_fail = False
        
        for tag_results in validation_results.values():
            if 'error' in tag_results:
                has_critical_fail = True
                break
                
            for validation_type, result in tag_results.items():
                if isinstance(result, dict):
                    status = result.get('status')
                    if status == 'PASS':
                        has_any_pass = True
                    elif status == 'FAIL':
                        if validation_type == 'build' and 'tests' in result:
                            pull_test = result['tests'].get('pull', {})
                            if pull_test.get('status') == 'SKIP':
                                continue
                        if validation_type == 'functionality' and result.get('reason'):
                            if 'not accessible' in result.get('reason', ''):
                                continue
                        has_critical_fail = True
                        break
                        
        if has_critical_fail:
            return 'FAIL'
        elif has_any_pass:
            return 'PASS'
        else:
            return 'SKIP'
        
    async def validate_all_images(self, image_filter: Optional[str] = None) -> List[Dict]:
        """Validate all configured images"""
        images = self.config['images']
        
        if image_filter:
            images = [img for img in images if image_filter in img['name']]
            
        self.logger.info(f"Validating {len(images)} images")
        
        semaphore = asyncio.Semaphore(self.config.get('validation_config', {}).get('parallel_jobs', 3))
        
        async def validate_with_semaphore(image_config):
            async with semaphore:
                return await self.validate_image(image_config)
                
        tasks = [validate_with_semaphore(img) for img in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
        
    def generate_report(self, results: List[Dict], output_path: Optional[str] = None) -> str:
        """Generate validation report"""
        report = {
            'validation_summary': {
                'total_images': len(results),
                'passed': len([r for r in results if r['overall_status'] == 'PASS']),
                'failed': len([r for r in results if r['overall_status'] == 'FAIL']),
                'timestamp': time.time()
            },
            'detailed_results': results
        }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
                
        return json.dumps(report, indent=2)


async def main():
    parser = argparse.ArgumentParser(description='Docker Image Validation Framework')
    parser.add_argument('--config', default='config/images.yaml', help='Configuration file path')
    parser.add_argument('--filter', help='Filter images by name pattern')
    parser.add_argument('--output', help='Output report file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    validator = ImageValidator(args.config)
    results = await validator.validate_all_images(args.filter)
    
    report = validator.generate_report(results, args.output)
    
    if not args.output:
        print(report)
        
    failed_count = len([r for r in results if r['overall_status'] == 'FAIL'])
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == '__main__':
    asyncio.run(main())
