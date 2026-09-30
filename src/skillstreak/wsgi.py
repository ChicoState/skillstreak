"""WSGI configuration for SkillStreak."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillstreak.settings.local")

application = get_wsgi_application()
