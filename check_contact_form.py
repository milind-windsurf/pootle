import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'contact_form',
    ],
    SECRET_KEY='test'
)
django.setup()

try:
    import contact_form
    print("contact_form module found")
    print("contact_form.__file__:", contact_form.__file__)
    print("contact_form.__version__:", getattr(contact_form, '__version__', 'unknown'))
    
    print("\nAvailable in contact_form:")
    for attr in dir(contact_form):
        if not attr.startswith('_'):
            print(f"  {attr}")
    
    try:
        from contact_form import views
        print("\nAvailable in contact_form.views:")
        for attr in dir(views):
            if not attr.startswith('_'):
                print(f"  {attr}")
    except ImportError as e:
        print(f"\nCannot import contact_form.views: {e}")
        
except ImportError as e:
    print(f"Cannot import contact_form: {e}")
