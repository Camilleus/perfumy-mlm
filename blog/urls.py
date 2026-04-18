from django.urls import path
from . import views

urlpatterns = [
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/generuj/', views.blog_generate, name='blog_generate'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
]