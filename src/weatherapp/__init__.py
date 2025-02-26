import logging

from django.conf import settings

logging.basicConfig(
    level=getattr(settings, 'LOG_LEVEL', logging.INFO),
    format='%(asctime)s %(name)s (%(levelname)s): %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
