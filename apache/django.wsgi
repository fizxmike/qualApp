import os
import sys
path = '/home/django'
if path not in sys.path:
    sys.path.append(path)
    
path = '/home/django/qualPrep'
if path not in sys.path:
    sys.path.append(path)
    
os.environ['DJANGO_SETTINGS_MODULE'] = 'qualPrep.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
