class SubscriptionCheckMiddleware:
    """
    En cada request del panel de negocio, verifica el estado de suscripción.
    Si está vencida, redirige a billing con aviso (excepto rutas de billing y auth).

    Optimizaciones de rendimiento:
    - El estado de suscripción se cachea en Redis 5 min → evita DB write por request.
    - El objeto Business se guarda en request.user.__dict__ → resto del request sin query.
    """
    EXEMPT_PATHS = ['/auth/', '/superadmin/', '/negocio/billing/', '/tienda/', '/static/', '/media/']
    # Cuántos segundos cachear el estado de la suscripción por usuario
    _SUB_CACHE_TTL = 300

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.is_business_owner
            and not any(request.path.startswith(p) for p in self.EXEMPT_PATHS)
        ):
            from django.core.cache import cache
            from apps.accounts.models import Business

            cache_key = f'sub_status_{request.user.pk}'
            sub_status = cache.get(cache_key)

            if sub_status is None:
                # Cache miss: consultar DB y calcular estado
                try:
                    business = Business.objects.select_related('saas_subscription').get(
                        owner=request.user
                    )
                    request.user.__dict__['business'] = business
                    sub = getattr(business, 'saas_subscription', None)
                    if sub:
                        sub.update_status()
                        sub_status = sub.status
                    else:
                        sub_status = 'active'
                except Business.DoesNotExist:
                    sub_status = 'active'
                cache.set(cache_key, sub_status, self._SUB_CACHE_TTL)
            else:
                # Cache hit: evitar re-query de Business si ya lo tenemos
                if 'business' not in request.user.__dict__:
                    try:
                        business = Business.objects.select_related('saas_subscription').get(
                            owner=request.user
                        )
                        request.user.__dict__['business'] = business
                    except Business.DoesNotExist:
                        pass

            if sub_status in ['expired', 'suspended']:
                from django.shortcuts import redirect
                return redirect('billing:expired')

        return self.get_response(request)
