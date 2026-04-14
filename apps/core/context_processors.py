from django.core.cache import cache


def business_context(request):
    """Inyecta datos del negocio en todos los templates del panel."""
    context = {}
    if (request.user.is_authenticated
            and request.user.is_business_owner
            and request.user.has_business):
        from apps.orders.models import Order
        business = request.user.business
        cache_key = f'pending_orders_{business.pk}'
        count = cache.get(cache_key)
        if count is None:
            count = Order.objects.filter(
                business=business,
                status='pending',
            ).count()
            cache.set(cache_key, count, 20)  # refresca cada 20 segundos
        context['pending_orders_count'] = count
        context['unread_notifications_count'] = 0
    return context
