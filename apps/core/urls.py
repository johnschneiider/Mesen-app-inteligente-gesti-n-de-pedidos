from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('sidebar/', views.ToggleSidebarView.as_view(), name='toggle_sidebar'),
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
]
