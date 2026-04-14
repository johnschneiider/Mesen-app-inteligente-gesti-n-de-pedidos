from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View


class HomeView(View):
    """
    Para usuarios anónimos: cachea el HTML renderizado directamente en Redis
    (cache_page no funciona con Vary:Cookie del SessionMiddleware).
    """
    _CACHE_KEY = 'homepage_html_v2'
    _CACHE_TTL = 1800  # 30 minutos

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_superadmin:
                return redirect('superadmin:dashboard')
            if request.user.is_business_owner and request.user.has_business:
                return redirect('orders:dashboard')

        cached = cache.get(self._CACHE_KEY)
        if cached is not None:
            resp = HttpResponse(cached, content_type='text/html; charset=utf-8')
            resp['Cache-Control'] = 'public, max-age=1800'
            resp['X-Cache'] = 'HIT'
            return resp

        response = render(request, 'core/home.html')
        cache.set(self._CACHE_KEY, response.content, self._CACHE_TTL)
        response['Cache-Control'] = 'public, max-age=1800'
        response['X-Cache'] = 'MISS'
        return response


class ToggleSidebarView(View):
    def get(self, request):
        return render(request, 'components/sidebar.html')


class NotificationsView(View):
    def get(self, request):
        return render(request, 'components/notifications.html', {'notifications': []})
