from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<int:pk>/cerrar/', views.CloseTicketView.as_view(), name='close'),
]
