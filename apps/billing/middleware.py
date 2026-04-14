class SubscriptionCheckMiddleware:
    """
    Verifica suscripción y pre-cachea el objeto Business en request.user.__dict__
    para que sidebar, navbar y context_processor NO hagan queries adicionales.
    """
    EXEMPT_PATHS = ('/auth/', '/superadmin/', '/negocio/billing/', '/tienda/', '/static/', '/media/')
    _SUB_CACHE_TTL = 300  # 5 min

    def __init__(self, get_response):
        self.get_response = get_response

    def _load_business(self, user):
        """Carga Business + SaaSSubscription en 1 query y lo cachea en user.__dict__."""
        from apps.accounts.models import Business
        try:
            business = Business.objects.select_related('saas_subscription').get(owner=user)
            user.__dict__['business'] = business
            return business
        except Business.DoesNotExist:
            return None

    def __call__(self, request):
        user = request.user
        if not user.is_authenticated or not user.is_business_owner:
            return self.get_response(request)

        # Siempre pre-cargar business para evitar lazy queries en templates
        business = self._load_business(user)

        # Solo verificar suscripción si NO es ruta exenta
        if business and not request.path.startswith(self.EXEMPT_PATHS):
            from django.core.cache import cache

            cache_key = f'sub_status_{user.pk}'
            sub_status = cache.get(cache_key)

            if sub_status is None:
                sub = getattr(business, 'saas_subscription', None)
                if sub:
                    sub.update_status()
                    sub_status = sub.status
                else:
                    sub_status = 'none'
                cache.set(cache_key, sub_status, self._SUB_CACHE_TTL)

            if sub_status in ('expired', 'suspended'):
                from django.shortcuts import redirect
                return redirect('billing:expired')

        return self.get_response(request)
