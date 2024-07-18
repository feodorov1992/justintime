import os
from django import template
from django.urls import reverse

from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def static(context, path):
    if settings.DEBUG:
        return os.path.join(settings.STATICFILES_DIRS[0], path)
    return os.path.join(settings.STATIC_ROOT, path)


@register.simple_tag(takes_context=True)
def media(context, path):
    return f'{settings.BASE_DIR}/media/{path}'
