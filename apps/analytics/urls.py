from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('ventas-json/', views.SalesChartDataView.as_view(), name='sales_json'),
    path('clientes-json/', views.TopClientsDataView.as_view(), name='clients_json'),
    path('pagos-json/', views.PaymentRatioDataView.as_view(), name='payments_json'),
]
