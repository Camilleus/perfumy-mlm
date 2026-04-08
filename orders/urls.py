from django.urls import path
from . import views

urlpatterns = [
    path('koszyk/', views.cart_detail, name='cart_detail'),
    path('koszyk/dodaj/<int:pk>/', views.cart_add, name='cart_add'),
    path('koszyk/usun/<int:pk>/', views.cart_remove, name='cart_remove'),
]