import allauth
print("Allauth version:", allauth.__version__)

from allauth.socialaccount import helpers
print("Available functions in helpers:")
for attr in dir(helpers):
    if not attr.startswith('_'):
        print(f"  {attr}")

print("\nFunctions containing 'add':")
for attr in dir(helpers):
    if 'add' in attr.lower():
        print(f"  {attr}")
