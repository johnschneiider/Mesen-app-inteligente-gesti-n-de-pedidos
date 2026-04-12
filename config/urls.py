from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

urlpatterns = [
    path('', include('apps.core.urls')),
    path('auth/', include('apps.accounts.urls', namespace='accounts')),
    path('negocio/', include('apps.orders.urls', namespace='orders')),
    path('negocio/menu/', include('apps.menus.urls', namespace='menus')),
    path('negocio/sub/', include('apps.subscriptions.urls', namespace='subscriptions')),
    path('negocio/analitica/', include('apps.analytics.urls', namespace='analytics')),
    path('negocio/soporte/', include('apps.support.urls', namespace='support')),
    path('negocio/billing/', include('apps.billing.urls', namespace='billing')),
    path('tienda/', include('apps.store.urls', namespace='store')),
    path('superadmin/', include('apps.superadmin.urls', namespace='superadmin')),
    # Silence Chrome DevTools auto-request in dev logs
    path('.well-known/appspecific/com.chrome.devtools.json', lambda r: HttpResponse('{}', content_type='application/json')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
