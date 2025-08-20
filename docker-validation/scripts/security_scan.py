#!/usr/bin/env python3
"""
Security scanning module for Docker images
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List


class SecurityScanner:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def scan(self, image_name: str) -> Dict:
        """Run security scan on Docker image"""
        results = {
            'image': image_name,
            'scans': {},
            'overall_status': 'PENDING'
        }
        
        try:
            trivy_result = await self._run_trivy_scan(image_name)
            results['scans']['trivy'] = trivy_result
            
            scout_result = await self._run_docker_scout_scan(image_name)
            results['scans']['docker_scout'] = scout_result
            
            results['overall_status'] = self._determine_security_status(results['scans'])
            
        except Exception as e:
            self.logger.error(f"Security scan failed for {image_name}: {e}")
            results['error'] = str(e)
            results['overall_status'] = 'FAIL'
            
        return results
        
    async def _run_trivy_scan(self, image_name: str) -> Dict:
        """Run Trivy vulnerability scan"""
        try:
            cmd = [
                'trivy', 'image', '--format', 'json',
                '--severity', 'HIGH,CRITICAL',
                '--exit-code', '0',
                image_name
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                scan_data = json.loads(stdout.decode())
                return {
                    'status': 'PASS',
                    'tool': 'trivy',
                    'vulnerabilities': self._parse_trivy_results(scan_data),
                    'raw_output': scan_data
                }
            else:
                return {
                    'status': 'FAIL',
                    'tool': 'trivy',
                    'error': stderr.decode(),
                    'return_code': process.returncode
                }
                
        except FileNotFoundError:
            self.logger.warning("Trivy not found, skipping scan")
            return {
                'status': 'SKIP',
                'tool': 'trivy',
                'error': 'Trivy not installed'
            }
        except Exception as e:
            return {
                'status': 'FAIL',
                'tool': 'trivy',
                'error': str(e)
            }
            
    async def _run_docker_scout_scan(self, image_name: str) -> Dict:
        """Run Docker Scout security scan"""
        try:
            cmd = [
                'docker', 'scout', 'cves', '--format', 'json',
                '--only-severity', 'high,critical',
                image_name
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                try:
                    scan_data = json.loads(stdout.decode())
                    return {
                        'status': 'PASS',
                        'tool': 'docker_scout',
                        'vulnerabilities': self._parse_scout_results(scan_data),
                        'raw_output': scan_data
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'PASS',
                        'tool': 'docker_scout',
                        'vulnerabilities': [],
                        'raw_output': stdout.decode()
                    }
            else:
                return {
                    'status': 'FAIL',
                    'tool': 'docker_scout',
                    'error': stderr.decode(),
                    'return_code': process.returncode
                }
                
        except FileNotFoundError:
            self.logger.warning("Docker Scout not found, skipping scan")
            return {
                'status': 'SKIP',
                'tool': 'docker_scout',
                'error': 'Docker Scout not available'
            }
        except Exception as e:
            return {
                'status': 'FAIL',
                'tool': 'docker_scout',
                'error': str(e)
            }
            
    def _parse_trivy_results(self, scan_data: Dict) -> List[Dict]:
        """Parse Trivy scan results"""
        vulnerabilities = []
        
        if 'Results' in scan_data:
            for result in scan_data['Results']:
                if 'Vulnerabilities' in result:
                    for vuln in result['Vulnerabilities']:
                        vulnerabilities.append({
                            'id': vuln.get('VulnerabilityID'),
                            'severity': vuln.get('Severity'),
                            'package': vuln.get('PkgName'),
                            'version': vuln.get('InstalledVersion'),
                            'fixed_version': vuln.get('FixedVersion'),
                            'title': vuln.get('Title'),
                            'description': vuln.get('Description')
                        })
                        
        return vulnerabilities
        
    def _parse_scout_results(self, scan_data: Dict) -> List[Dict]:
        """Parse Docker Scout scan results"""
        vulnerabilities = []
        
        if isinstance(scan_data, dict) and 'vulnerabilities' in scan_data:
            for vuln in scan_data['vulnerabilities']:
                vulnerabilities.append({
                    'id': vuln.get('id'),
                    'severity': vuln.get('severity'),
                    'package': vuln.get('package', {}).get('name'),
                    'version': vuln.get('package', {}).get('version'),
                    'fixed_version': vuln.get('fixed_version'),
                    'title': vuln.get('title'),
                    'description': vuln.get('description')
                })
                
        return vulnerabilities
        
    def _determine_security_status(self, scans: Dict) -> str:
        """Determine overall security status"""
        for scan_name, scan_result in scans.items():
            if scan_result.get('status') == 'FAIL':
                return 'FAIL'
                
            vulnerabilities = scan_result.get('vulnerabilities', [])
            critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'CRITICAL']
            
            if critical_vulns:
                return 'FAIL'
                
        return 'PASS'
