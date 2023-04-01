from django import template

register = template.Library()

@register.inclusion_tag('external_badge.html')
def externalbadge(host):
    return {'host': host}
