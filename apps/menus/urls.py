from django.urls import path
from . import views

app_name = 'menus'

urlpatterns = [
    path('', views.MenuListView.as_view(), name='list'),
    path('nuevo/', views.MenuCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.MenuUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.MenuDeleteView.as_view(), name='delete'),
    path('<int:pk>/foto/', views.AddMenuPhotoView.as_view(), name='add_photo'),
    path('<int:pk>/ingrediente/', views.AddIngredientView.as_view(), name='add_ingredient'),
    path('ingrediente/<int:pk>/', views.RemoveIngredientView.as_view(), name='remove_ingredient'),
]
