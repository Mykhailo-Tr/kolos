from django import template
from django.utils.safestring import mark_safe
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def sort_link(request, field, label):
    params = request.GET.copy()
    current_order = params.get("order")

    if current_order == field:
        new_order = f"-{field}"
        arrow = "▲"
    elif current_order == f"-{field}":
        new_order = field
        arrow = "▼"
    else:
        new_order = field
        arrow = "⇅"

    params["order"] = new_order
    query = urlencode(params)
    url = f"?{query}" if query else "?"

    html = f'<a href="{url}" class="sort-link">{label} <span class="sort-arrow">{arrow}</span></a>'
    return mark_safe(html)
