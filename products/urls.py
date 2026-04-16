from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('produkt/<slug:slug>/', views.product_detail, name='product_detail'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz/reset/', views.quiz_reset, name='quiz_reset'),
]