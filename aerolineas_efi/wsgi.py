"""
WSGI config for aerolineas_efi project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aerolineas_efi.settings')

application = get_wsgi_application()
