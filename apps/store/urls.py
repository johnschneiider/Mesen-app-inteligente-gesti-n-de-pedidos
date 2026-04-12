from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('<slug:slug>/', views.StoreView.as_view(), name='store'),
    path('<slug:slug>/menu/<int:pk>/pedir/', views.CreateOrderView.as_view(), name='create_order'),
    path('<slug:slug>/menu/<int:pk>/', views.MenuDetailView.as_view(), name='menu_detail'),
    path('<slug:slug>/menu/<int:pk>/auth/', views.StoreQuickAuthView.as_view(), name='quick_auth'),
    path('<slug:slug>/menu/<int:pk>/rating/', views.RateMenuView.as_view(), name='rate_menu'),
    path('<slug:slug>/suscripciones/', views.StoreSubscriptionsView.as_view(), name='subscriptions'),
    path('<slug:slug>/suscribirse/', views.SubscribeView.as_view(), name='subscribe'),
    path('<slug:slug>/resena/', views.SubmitReviewView.as_view(), name='submit_review'),
]
