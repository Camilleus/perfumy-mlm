from .models import Product
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.db.models import Q, Min, Max


def product_list(request):
    products = Product.objects.filter(is_available=True)

    # --- FILTRY ---
    gender = request.GET.get('gender', '')
    brands_selected = request.GET.getlist('brands')          # lista wybranych marek
    category = request.GET.get('category', '')
    concentration = request.GET.get('concentration', '')
    occasion = request.GET.get('occasion', '')
    intensity = request.GET.get('intensity', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')

    if gender:
        products = products.filter(gender=gender)
    if brands_selected:
        products = products.filter(brand__in=brands_selected)
    if category:
        products = products.filter(category=category)
    if concentration:
        products = products.filter(concentration=concentration)
    if occasion:
        products = products.filter(occasion=occasion)
    if intensity:
        products = products.filter(intensity=intensity)
    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # --- SORTOWANIE ---
    sort_by = request.GET.get('sort', 'name_asc')
    sort_map = {
        'price_asc': 'price',
        'price_desc': '-price',
        'name_asc': 'name',
        'name_desc': '-name',
        'newest': '-id',
    }
    products = products.order_by(sort_map.get(sort_by, 'name'))

    # --- PAGINACJA ---
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    try:
        products_page = paginator.page(page)
    except:
        products_page = paginator.page(1)

    # --- DANE DLA FILTRÓW ---
    all_products = Product.objects.filter(is_available=True)
    all_brands = all_products.values_list('brand', flat=True).distinct().order_by('brand')
    price_range = all_products.aggregate(min=Min('price'), max=Max('price'))

    return render(request, 'products/list.html', {
        'products': products_page,
        'page_obj': products_page,
        'brands': all_brands,                     # lista wszystkich marek do checkboxów
        'selected_brands': brands_selected,       # lista wybranych marek
        'price_range': price_range,
        # choices dla filtrów
        'categories': Product.CATEGORY_CHOICES,
        'concentrations': Product.CONCENTRATION_CHOICES,
        'occasions': Product.OCCASION_CHOICES,
        'intensities': Product.INTENSITY_CHOICES,
        # aktywne filtry (dla pojedynczych wartości)
        'current_sort': sort_by,
        'current_gender': gender,
        'current_category': category,
        'current_concentration': concentration,
        'current_occasion': occasion,
        'current_intensity': intensity,
        'current_price_min': price_min,
        'current_price_max': price_max,
        # liczba wyników
        'total_count': paginator.count,
    })

def product_detail(request, slug):
    import json
    import threading
    import anthropic
    from django.conf import settings

    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.all()
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0

    # Parsuj FAQ z bazy
    faq_items = []
    if product.faq_json:
        try:
            faq_items = json.loads(product.faq_json)
        except Exception:
            faq_items = []

    # Generuj FAQ w tle jeśli go nie ma
    if not product.faq_json:
        def generate_faq():
            try:
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                prompt = f"""Jesteś ekspertem perfumerii. Napisz 4 pytania i odpowiedzi FAQ dla tych perfum.

Produkt: {product.name}
Marka: {product.brand}
Rodzaj: {product.get_gender_display()}
Nuty zapachowe: {product.scent_notes or 'brak danych'}
Koncentracja: {product.get_concentration_display()}
Okazja: {product.get_occasion_display() if product.occasion else 'różne'}
Intensywność: {product.get_intensity_display() if product.intensity else 'różne'}
Cena: {product.price} zł

Pytania muszą być konwersacyjne, naturalne, takie jak zadałaby Gen Z głosowo.
Przykłady: "Czy {product.name} nadaje się na randkę?", "Jak długo trzymają się {product.name}?", "Dla kogo są {product.name}?"

Odpowiedz TYLKO w formacie JSON, bez żadnego tekstu przed ani po:
[
  {{"q": "pytanie 1", "a": "odpowiedź 1"}},
  {{"q": "pytanie 2", "a": "odpowiedź 2"}},
  {{"q": "pytanie 3", "a": "odpowiedź 3"}},
  {{"q": "pytanie 4", "a": "odpowiedź 4"}}
]"""

                message = client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=800,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                raw = message.content[0].text.strip()
                # Upewnij się że to valid JSON
                parsed = json.loads(raw)
                product.faq_json = json.dumps(parsed, ensure_ascii=False)
                product.save(update_fields=['faq_json'])
            except Exception as e:
                pass

        t = threading.Thread(target=generate_faq)
        t.daemon = True
        t.start()

    return render(request, 'products/detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'faq_items': faq_items,
    })


def quiz(request):
    if request.method == 'POST':
        request.session['quiz_intensity'] = request.POST.get('intensity')
        request.session['quiz_category'] = request.POST.get('category')
        request.session['quiz_occasion'] = request.POST.get('occasion')
        request.session['quiz_gender'] = request.POST.get('gender')
        return redirect('quiz')

    intensity = request.session.get('quiz_intensity')
    category = request.session.get('quiz_category')
    occasion = request.session.get('quiz_occasion')
    gender = request.session.get('quiz_gender')

    results = None
    if intensity and occasion:
        results = Product.objects.filter(
            is_available=True,
            intensity=intensity,
            occasion=occasion,
        )
        if category:
            results = results.filter(category=category)
        if gender:
            results = results.filter(gender=gender)

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
        'results': results_page,
        'page_obj': results_page,
    })


def quiz_reset(request):
    for key in list(request.session.keys()):
        if key.startswith('quiz_'):
            del request.session[key]
    return redirect('quiz')