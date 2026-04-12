def business_context(request):
    """Inyecta datos del negocio en todos los templates del panel."""
    context = {}
    if (request.user.is_authenticated
            and request.user.is_business_owner
            and request.user.has_business):
        from apps.orders.models import Order
        context['pending_orders_count'] = Order.objects.filter(
            business=request.user.business,
            status='pending',
        ).count()
        context['unread_notifications_count'] = 0
    return context
