from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


@method_decorator(cache_page(60 * 60), name='dispatch')  # 1 hora en cache (solo usuarios anónimos)
class HomeView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_superadmin:
                return redirect('superadmin:dashboard')
            if request.user.is_business_owner and request.user.has_business:
                return redirect('orders:dashboard')
        return render(request, 'core/home.html')


class ToggleSidebarView(View):
    def get(self, request):
        return render(request, 'components/sidebar.html')


class NotificationsView(View):
    def get(self, request):
        return render(request, 'components/notifications.html', {'notifications': []})
