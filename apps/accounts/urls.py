from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/modal/', views.LoginModalView.as_view(), name='login_modal'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/validate/phone/', views.ValidatePhoneView.as_view(), name='validate_phone'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('upgrade/', views.UpgradeToBusinessView.as_view(), name='upgrade_to_business'),
    # Consumer account
    path('mi-cuenta/', views.ConsumerDashboardView.as_view(), name='consumer_dashboard'),
    path('mi-cuenta/editar/', views.ConsumerEditView.as_view(), name='consumer_edit'),
    path('mi-cuenta/direccion/agregar/', views.AddAddressView.as_view(), name='add_address'),
    path('mi-cuenta/direccion/<int:pk>/eliminar/', views.DeleteAddressView.as_view(), name='delete_address'),
    path('mi-cuenta/direccion/<int:pk>/predeterminar/', views.SetDefaultAddressView.as_view(), name='set_default_address'),
]
