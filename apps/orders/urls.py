from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('pedidos/', views.OrderListView.as_view(), name='list'),
    path('pedidos/en-vivo/', views.LiveOrdersView.as_view(), name='live'),
    path('pedidos/confirmar-todos/', views.ConfirmAllPendingView.as_view(), name='confirm_all'),
    path('pedidos/<int:pk>/estado/', views.ChangeOrderStatusView.as_view(), name='change_status'),
    path('pedidos/<int:pk>/pagar/', views.MarkOrderPaidView.as_view(), name='mark_paid'),
    path('clientes/', views.ClientListView.as_view(), name='clients'),
    path('buscar/', views.OrderSearchView.as_view(), name='search'),
]
