from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    path('', views.SuperAdminDashboardView.as_view(), name='dashboard'),
    path('negocios/', views.BusinessListView.as_view(), name='business_list'),
    path('negocios/<int:pk>/', views.BusinessDetailView.as_view(), name='business_detail'),
    path('negocios/<int:pk>/suscripcion/', views.EditSubscriptionView.as_view(), name='edit_subscription'),
    path('negocios/<int:pk>/features/', views.EditFeaturesView.as_view(), name='edit_features'),
    path('negocios/<int:pk>/suspender/', views.SuspendBusinessView.as_view(), name='suspend'),
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
]
