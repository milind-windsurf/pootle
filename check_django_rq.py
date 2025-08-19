import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django_rq',
    ],
    SECRET_KEY='test',
    RQ_QUEUES={
        'default': {
            'HOST': 'localhost',
            'PORT': 6379,
            'DB': 0,
        }
    }
)
django.setup()

try:
    import django_rq
    print("django_rq version:", getattr(django_rq, '__version__', 'unknown'))
    
    from django_rq import queues
    print("\nAvailable in django_rq.queues:")
    for attr in dir(queues):
        if not attr.startswith('_'):
            print(f"  {attr}")
    
    print("\nFunctions containing 'failed':")
    for attr in dir(queues):
        if 'failed' in attr.lower():
            print(f"  {attr}")
            
    try:
        from django_rq.queues import get_queue
        print(f"\nget_queue found: {get_queue}")
        
        queue = get_queue('default')
        print(f"Queue methods containing 'failed': {[m for m in dir(queue) if 'failed' in m.lower()]}")
    except Exception as e:
        print(f"\nError getting queue: {e}")
        
except ImportError as e:
    print(f"Cannot import django_rq: {e}")
