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


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'products/detail.html', {'product': product})

def quiz(request):
    results = None
    if request.method == 'POST':
        intensity = request.POST.get('intensity')
        category = request.POST.get('category')
        occasion = request.POST.get('occasion')
        gender = request.POST.get('gender')
        results = Product.objects.filter(
            is_available=True,
            intensity=intensity,
            occasion=occasion,
        )
        if category:
            results = results.filter(category=category)
        if gender:
            results = results.filter(gender=gender)
    return render(request, 'products/quiz.html', {'results': results})