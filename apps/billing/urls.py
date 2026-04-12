from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.BillingDetailView.as_view(), name='detail'),
    path('vencida/', views.SubscriptionExpiredView.as_view(), name='expired'),
]
