from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def active_nav(context, url_name):
    request = context.get('request')
    if request and request.resolver_match:
        current = request.resolver_match.url_name
        view_name = request.resolver_match.view_name
        if url_name in view_name or url_name == current:
            return 'active'
    return ''


@register.filter
def currency_cop(value):
    """Formatea un entero como moneda COP."""
    try:
        return f'${int(value):,}'.replace(',', '.')
    except (ValueError, TypeError):
        return value


@register.filter
def initials(value):
    """Obtiene las iniciales de un nombre."""
    if not value:
        return ''
    parts = str(value).strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return str(value)[:2].upper()


@register.inclusion_tag('components/nav_item.html', takes_context=True)
def nav_item(context, url_name, label, icon='', badge=None, disabled=False):
    request = context.get('request')
    is_active = False
    if request and request.resolver_match:
        full_name = request.resolver_match.view_name
        is_active = url_name.replace(':', '_') in full_name.replace(':', '_')
    return {
        'url_name': url_name,
        'label': label,
        'icon': icon,
        'badge': badge,
        'disabled': disabled,
        'is_active': is_active,
        'request': request,
    }
