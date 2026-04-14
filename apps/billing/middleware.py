class SubscriptionCheckMiddleware:
    """
    En cada request del panel de negocio, verifica el estado de suscripción.
    Si está vencida, redirige a billing con aviso (excepto rutas de billing y auth).
    """
    EXEMPT_PATHS = ['/auth/', '/superadmin/', '/negocio/billing/', '/tienda/', '/static/', '/media/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.is_business_owner
            and not any(request.path.startswith(p) for p in self.EXEMPT_PATHS)
        ):
            # Carga negocio + suscripción en una sola query con select_related
            from apps.accounts.models import Business
            try:
                business = Business.objects.select_related('saas_subscription').get(owner=request.user)
                # Cacheamos en el objeto user para que el resto del request no re-query
                request.user.__dict__['business'] = business
                sub = getattr(business, 'saas_subscription', None)
                if sub:
                    sub.update_status()
                    if sub.status in ['expired', 'suspended']:
                        from django.shortcuts import redirect
                        return redirect('billing:expired')
            except Business.DoesNotExist:
                pass

        return self.get_response(request)
