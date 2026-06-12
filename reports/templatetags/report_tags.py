from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return the value for a given dictionary key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''
