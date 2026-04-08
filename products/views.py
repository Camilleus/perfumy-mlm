from django.shortcuts import render
from .models import Product

def product_list(request):
    products = Product.objects.filter(is_available=True)
    
    gender = request.GET.get('gender')
    brand = request.GET.get('brand')
    
    if gender:
        products = products.filter(gender=gender)
    if brand:
        products = products.filter(brand__icontains=brand)
    
    brands = Product.objects.filter(is_available=True).values_list('brand', flat=True).distinct()
    
    return render(request, 'products/list.html', {
        'products': products,
        'brands': brands,
    })