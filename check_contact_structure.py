import sys
import os

site_packages = "/home/ubuntu/.pyenv/versions/3.12.8/lib/python3.12/site-packages"

print("Looking for contact-related packages:")
for item in os.listdir(site_packages):
    if 'contact' in item.lower():
        print(f"  {item}")
        item_path = os.path.join(site_packages, item)
        if os.path.isdir(item_path):
            print(f"    Contents: {os.listdir(item_path)[:10]}")  # First 10 items

import_attempts = [
    "contact_form",
    "django_contact_form", 
    "contact_form.views",
    "django_contact_form.views"
]

for attempt in import_attempts:
    try:
        module = __import__(attempt, fromlist=[''])
        print(f"\nSuccessfully imported: {attempt}")
        print(f"  Module file: {getattr(module, '__file__', 'unknown')}")
        print(f"  Available attributes: {[x for x in dir(module) if not x.startswith('_')][:10]}")
        
        if hasattr(module, 'ContactFormView'):
            print(f"  Found ContactFormView!")
        elif 'views' in attempt:
            print(f"  No ContactFormView found in {attempt}")
            
    except ImportError as e:
        print(f"\nFailed to import {attempt}: {e}")
