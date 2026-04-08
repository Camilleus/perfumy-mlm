from django.shortcuts import render
from .models import Product
from django.shortcuts import get_object_or_404

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


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/detail.html', {'product': product})

def quiz(request):
    return render(request, 'products/quiz.html')