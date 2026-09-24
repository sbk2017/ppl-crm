"""
ASGI config for the Prestige Pulse Cargo CRM project.
Included for completeness — this project runs under WSGI (Gunicorn),
so ASGI is not actively used. Harmless to keep for future tooling.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()