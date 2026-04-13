from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<int:pk>/', views.order_confirmation, name='order_confirmation'),
    path('cart/increase/<int:pk>/', views.cart_increase, name='cart_increase'),
    path('cart/decrease/<int:pk>/', views.cart_decrease, name='cart_decrease'),
]
