from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.SubscriptionListView.as_view(), name='list'),
    path('nuevo/', views.SubscriptionPlanCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.SubscriptionPlanUpdateView.as_view(), name='update'),
    path('cliente/<int:pk>/confirmar/', views.ConfirmClientSubscriptionView.as_view(), name='confirm'),
]
