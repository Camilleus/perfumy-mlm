from .models import Product
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.db.models import Q

def product_list(request):
    products = Product.objects.filter(is_available=True)

    # Filtrowanie (istniejące)
    gender = request.GET.get('gender')
    if gender:
        products = products.filter(gender=gender)

    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand__icontains=brand)

    # Nowe: sortowanie
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    elif sort_by == 'newest':
        products = products.order_by('-id')  # lub '-created_at' jeśli masz
    else:
        products = products.order_by('name')  # domyślnie po nazwie

    # Paginacja
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    try:
        products_page = paginator.page(page)
    except:
        products_page = paginator.page(1)

    # Pobierz unikalne marki dla filtra
    brands = Product.objects.filter(is_available=True).values_list('brand', flat=True).distinct().order_by('brand')

    return render(request, 'products/list.html', {
        'products': products_page,
        'page_obj': products_page,
        'brands': brands,
        'current_brand': request.GET.get('brand', ''),
        'current_sort': sort_by,
        'current_gender': gender,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'products/detail.html', {'product': product})

def quiz(request):
    # Jeśli POST – zapisz odpowiedzi w sesji i przekieruj na GET
    if request.method == 'POST':
        request.session['quiz_intensity'] = request.POST.get('intensity')
        request.session['quiz_category'] = request.POST.get('category')
        request.session['quiz_occasion'] = request.POST.get('occasion')
        request.session['quiz_gender'] = request.POST.get('gender')
        return redirect('quiz')

    # Dla GET – odczytaj filtry z sesji
    intensity = request.session.get('quiz_intensity')
    category = request.session.get('quiz_category')
    occasion = request.session.get('quiz_occasion')
    gender = request.session.get('quiz_gender')

    results = None
    if intensity and occasion:   # wymagane pola
        results = Product.objects.filter(
            is_available=True,
            intensity=intensity,
            occasion=occasion,
        )
        if category:
            results = results.filter(category=category)
        if gender:
            results = results.filter(gender=gender)

    # Paginacja
    if results:
        paginator = Paginator(results, 24)
        page = request.GET.get('page')
        try:
            results_page = paginator.page(page)
        except PageNotAnInteger:
            results_page = paginator.page(1)
        except EmptyPage:
            results_page = paginator.page(paginator.num_pages)
    else:
        results_page = None

    return render(request, 'products/quiz.html', {
        'results': results_page,      # produkty (stronicowane)
        'page_obj': results_page,     # dla paginacji
    })


def quiz_reset(request):
    """Wyczyść wszystkie zapisane odpowiedzi quizu w sesji"""
    for key in list(request.session.keys()):
        if key.startswith('quiz_'):
            del request.session[key]
    return redirect('quiz')