from django.urls import path
from . import views

urlpatterns = [
    path('panel/', views.seller_panel, name='seller_panel'),
    path('rejestracja/', views.register, name='register'),
    path('rejestracja/<str:ref>/', views.register, name='register_with_ref'),
]