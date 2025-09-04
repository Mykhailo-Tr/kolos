from django import template

register = template.Library()


@register.filter
def pluck(queryset, key):
    """Витягує список значень по ключу з queryset/list of dicts"""
    return [item.get(key) for item in queryset if item.get(key) is not None]