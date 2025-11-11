from django import template

register = template.Library()

@register.filter
def getattr(obj, field_name):
    """Отримує значення поля об'єкта по назві"""
    return getattr(obj, field_name, "")
