from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from products.models import Product
from orders.models import Order
from .models import Review


def add_review(request, product_slug):
    if request.method != 'POST':
        return redirect('product_detail', slug=product_slug)

    product = get_object_or_404(Product, slug=product_slug)
    email = request.POST.get('email', '').strip()
    name = request.POST.get('name', '').strip()
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if not all([email, name, rating, comment]):
        return redirect('product_detail', slug=product_slug)

    # Sprawdź czy email był użyty w zamówieniu (Omnibus – zweryfikowany zakup)
    verified = Order.objects.filter(email=email).exists()

    Review.objects.create(
        product=product,
        email=email,
        name=name,
        rating=int(rating),
        comment=comment,
        verified_purchase=verified,
    )

    return redirect('product_detail', slug=product_slug)