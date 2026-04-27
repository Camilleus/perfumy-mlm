"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap
from products.models import Product
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
import django.views.i18n


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_available=True)

    def location(self, obj):
        return f'/produkt/{obj.slug}/'
    
class BrandSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        from django.utils.text import slugify
        brands = Product.objects.filter(is_available=True).values_list('brand', flat=True).distinct()
        return [slugify(b) for b in brands]

    def location(self, slug):
        return f'/perfumy/{slug}/'


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /panel/",
        "Disallow: /moje-zamowienia/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


sitemaps = {
    'products': ProductSitemap,
    'brands': BrandSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('', include('orders.urls')),
    path('', include('sellers.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('', include('policies.urls')),
    path('regulamin/', TemplateView.as_view(template_name='policies/regulamin.html'), name='regulamin'),
    path('polityka-prywatnosci/', TemplateView.as_view(template_name='policies/privacy_policy.html'), name='polityka_prywatnosci'),
    path('zwroty-reklamacje/', TemplateView.as_view(template_name='policies/returns_policy.html'), name='returns_policy'),
    path('odr/', TemplateView.as_view(template_name='policies/odr.html'), name='odr'),
    path('omnibus/', TemplateView.as_view(template_name='policies/omnibus.html'), name='omnibus'),
    path('kontakt/', TemplateView.as_view(template_name='policies/contact.html'), name='contact'),
    path('odstapienie-formularz/', TemplateView.as_view(template_name='policies/withdrawal_form.html'), name='withdrawal_form'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('o-nas/', TemplateView.as_view(template_name='policies/about.html'), name='about'),
    path('', include('reviews.urls')),
    path('', include('blog.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)