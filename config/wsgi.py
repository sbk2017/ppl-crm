"""
WSGI config for the Prestige Pulse Cargo CRM project.
Exposes the WSGI callable as a module-level variable named ``application``.
Used by Gunicorn in production: gunicorn config.wsgi:application
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()