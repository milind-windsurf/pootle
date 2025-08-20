#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import subprocess
import json
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate Docker images for existence, accessibility, and basic metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            'images',
            nargs='*',
            help='Docker images to validate (space-separated)'
        )
        parser.add_argument(
            '--file',
            dest='image_file',
            help='File containing list of Docker images (one per line)'
        )
        parser.add_argument(
            '--format',
            choices=['table', 'json'],
            default='table',
            help='Output format (default: table)'
        )

    def handle(self, *args, **options):
        images = self.get_images_list(options)
        
        if not images:
            raise CommandError("No Docker images provided. Use positional arguments or --file option.")

        self.stdout.write("Validating {0} Docker images...".format(len(images)))
        
        results = []
        for image in images:
            result = self.validate_image(image)
            results.append(result)
            
        self.output_results(results, options['format'])

    def get_images_list(self, options):
        images = list(options['images'])
        
        if options['image_file']:
            try:
                with open(options['image_file'], 'r') as f:
                    file_images = [line.strip() for line in f if line.strip()]
                    images.extend(file_images)
            except IOError as e:
                raise CommandError("Error reading image file: {0}".format(e))
                
        return images

    def validate_image(self, image):
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

    def output_results(self, results, format_type):
        if format_type == 'json':
            self.stdout.write(json.dumps(results, indent=2))
        else:
            self.output_table(results)

    def output_table(self, results):
        self.stdout.write("\n" + "="*100)
        self.stdout.write("{0:<40} {1:<15} {2:<15} {3:<20}".format('Image', 'Status', 'Size', 'Created'))
        self.stdout.write("="*100)
        
        for result in results:
            status = "[OK] Valid" if result['accessible'] else "[FAIL] Invalid"
            size = self.format_size(result['size']) if result['size'] else "N/A"
            created = result['created'][:19] if result['created'] else "N/A"
            
            self.stdout.write("{0:<40} {1:<15} {2:<15} {3:<20}".format(result['image'], status, size, created))
            
            if result['error']:
                self.stdout.write("  Error: {0}".format(result['error']))
        
        self.stdout.write("="*100)
        
        valid_count = sum(1 for r in results if r['accessible'])
        self.stdout.write("\nSummary: {0}/{1} images are valid and accessible".format(valid_count, len(results)))

    def format_size(self, size_bytes):
        if not size_bytes:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return "{0:.1f}{1}".format(size_bytes, unit)
            size_bytes /= 1024.0
        return "{0:.1f}TB".format(size_bytes)
