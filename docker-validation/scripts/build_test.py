#!/usr/bin/env python3
"""
Build validation module for Docker images
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List


class BuildValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def validate(self, image_name: str) -> Dict:
        """Validate Docker image build and configuration"""
        results = {
            'image': image_name,
            'tests': {},
            'overall_status': 'PENDING'
        }
        
        try:
            pull_result = await self._test_image_pull(image_name)
            results['tests']['pull'] = pull_result
            
            if pull_result['status'] == 'PASS':
                inspect_result = await self._test_image_inspect(image_name)
                results['tests']['inspect'] = inspect_result
                
                layers_result = await self._test_image_layers(image_name)
                results['tests']['layers'] = layers_result
                
                size_result = await self._test_image_size(image_name)
                results['tests']['size'] = size_result
                
            results['overall_status'] = self._determine_build_status(results['tests'])
            
        except Exception as e:
            self.logger.error(f"Build validation failed for {image_name}: {e}")
            results['error'] = str(e)
            results['overall_status'] = 'FAIL'
            
        return results
        
    async def _test_image_pull(self, image_name: str) -> Dict:
        """Test if image can be pulled successfully"""
        try:
            cmd = ['docker', 'pull', image_name]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'status': 'PASS' if process.returncode == 0 else 'FAIL',
                'return_code': process.returncode,
                'stdout': stdout.decode(),
                'stderr': stderr.decode()
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
            
    async def _test_image_inspect(self, image_name: str) -> Dict:
        """Inspect image configuration and metadata"""
        try:
            cmd = ['docker', 'inspect', image_name]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                inspect_data = json.loads(stdout.decode())
                image_info = inspect_data[0] if inspect_data else {}
                
                config = image_info.get('Config', {})
                
                analysis = {
                    'architecture': image_info.get('Architecture'),
                    'os': image_info.get('Os'),
                    'size': image_info.get('Size'),
                    'created': image_info.get('Created'),
                    'exposed_ports': list(config.get('ExposedPorts', {}).keys()),
                    'env_vars': config.get('Env', []),
                    'user': config.get('User'),
                    'working_dir': config.get('WorkingDir'),
                    'entrypoint': config.get('Entrypoint'),
                    'cmd': config.get('Cmd'),
                    'labels': config.get('Labels', {}),
                    'volumes': list(config.get('Volumes', {}).keys())
                }
                
                security_issues = self._check_security_best_practices(analysis)
                
                return {
                    'status': 'PASS',
                    'analysis': analysis,
                    'security_issues': security_issues,
                    'raw_data': image_info
                }
            else:
                return {
                    'status': 'FAIL',
                    'error': stderr.decode(),
                    'return_code': process.returncode
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
            
    async def _test_image_layers(self, image_name: str) -> Dict:
        """Analyze image layers for optimization"""
        try:
            cmd = ['docker', 'history', '--format', 'json', image_name]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                layers_data = []
                for line in stdout.decode().strip().split('\n'):
                    if line:
                        layers_data.append(json.loads(line))
                        
                analysis = {
                    'total_layers': len(layers_data),
                    'total_size': sum(layer.get('Size', 0) for layer in layers_data),
                    'large_layers': [
                        layer for layer in layers_data 
                        if layer.get('Size', 0) > 100 * 1024 * 1024
                    ]
                }
                
                return {
                    'status': 'PASS',
                    'analysis': analysis,
                    'layers': layers_data
                }
            else:
                return {
                    'status': 'FAIL',
                    'error': stderr.decode(),
                    'return_code': process.returncode
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
            
    async def _test_image_size(self, image_name: str) -> Dict:
        """Check image size and provide recommendations"""
        try:
            cmd = ['docker', 'images', '--format', 'json', image_name]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                images_data = []
                for line in stdout.decode().strip().split('\n'):
                    if line:
                        images_data.append(json.loads(line))
                        
                if images_data:
                    image_data = images_data[0]
                    size_str = image_data.get('Size', '0B')
                    size_bytes = self._parse_size_string(size_str)
                    
                    recommendations = []
                    if size_bytes > 1024 * 1024 * 1024:
                        recommendations.append("Image is larger than 1GB, consider optimization")
                    if size_bytes > 500 * 1024 * 1024:
                        recommendations.append("Consider using multi-stage builds")
                        
                    return {
                        'status': 'PASS',
                        'size_bytes': size_bytes,
                        'size_human': size_str,
                        'recommendations': recommendations,
                        'image_data': image_data
                    }
                else:
                    return {
                        'status': 'FAIL',
                        'error': 'No image data found'
                    }
            else:
                return {
                    'status': 'FAIL',
                    'error': stderr.decode(),
                    'return_code': process.returncode
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
            
    def _check_security_best_practices(self, analysis: Dict) -> List[str]:
        """Check for security best practices"""
        issues = []
        
        if not analysis.get('user') or analysis.get('user') == 'root':
            issues.append("Image runs as root user")
            
        if analysis.get('exposed_ports'):
            for port in analysis.get('exposed_ports', []):
                if '22/tcp' in port:
                    issues.append("SSH port exposed")
                    
        env_vars = analysis.get('env_vars', [])
        for env_var in env_vars:
            if any(keyword in env_var.upper() for keyword in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                issues.append(f"Potential secret in environment variable: {env_var}")
                
        return issues
        
    def _parse_size_string(self, size_str: str) -> int:
        """Parse Docker size string to bytes"""
        size_str = size_str.upper()
        
        if 'GB' in size_str:
            return int(float(size_str.replace('GB', '')) * 1024 * 1024 * 1024)
        elif 'MB' in size_str:
            return int(float(size_str.replace('MB', '')) * 1024 * 1024)
        elif 'KB' in size_str:
            return int(float(size_str.replace('KB', '')) * 1024)
        elif 'B' in size_str:
            return int(size_str.replace('B', ''))
        else:
            return 0
            
    def _determine_build_status(self, tests: Dict) -> str:
        """Determine overall build status"""
        for test_name, test_result in tests.items():
            if test_result.get('status') == 'FAIL':
                return 'FAIL'
                
        return 'PASS'
