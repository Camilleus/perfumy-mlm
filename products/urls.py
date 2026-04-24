from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('produkt/<slug:slug>/', views.product_detail, name='product_detail'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz/reset/', views.quiz_reset, name='quiz_reset'),
    # Static pages dla marek
    path('perfumy/<slug:brand_slug>/', views.brand_page, name='brand_page'),
    path('perfumy/<slug:brand_slug>/damskie/', views.brand_page, {'gender': 'K'}, name='brand_page_female'),
    path('perfumy/<slug:brand_slug>/meskie/', views.brand_page, {'gender': 'M'}, name='brand_page_male'),
    path('perfumy/<slug:brand_slug>/unisex/', views.brand_page, {'gender': 'U'}, name='brand_page_unisex'),
]