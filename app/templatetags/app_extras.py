from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
import re

register = template.Library()


@register.filter(name="addcss")
def addcss(field, css):
    return field.as_widget(attrs={"class": css})


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    try:
        pattern = '^' + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context['request'].path
    if re.search(pattern, path):
        return 'active'
    return ''
