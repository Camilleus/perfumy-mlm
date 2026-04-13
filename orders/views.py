from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from products.models import Product
from .cart import Cart
from .models import Order, OrderItem


def cart_add(request, pk):
    cart = Cart(request)
    product = Product.objects.get(pk=pk)
    cart.add(product)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def cart_remove(request, pk):
    cart = Cart(request)
    cart.remove(pk)
    return redirect('cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart.html', {'cart': cart})


def checkout(request):
    cart = Cart(request)

    if cart.count() == 0:
        return redirect('cart_detail')

    if request.method == 'POST':
        # Pobierz dane z formularza
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        note = request.POST.get('note', '')

        # Utwórz zamówienie
        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal_code,
            note=note,
            total_amount=cart.get_total(),
        )

        # Dodaj pozycje zamówienia
        for item in cart.get_items():
            product = Product.objects.get(pk=item['pk'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=item['price'],
            )

        # Wyślij email potwierdzający
        try:
            send_mail(
                subject=f'Potwierdzenie zamówienia #{order.pk} – Twoja Perfumka',
                message=f'''Cześć {first_name}!

Dziękujemy za zamówienie w Twoja Perfumka.

Numer zamówienia: #{order.pk}
Łączna kwota: {order.total_amount} zł
Płatność: za pobraniem

Adres dostawy:
{first_name} {last_name}
{address}
{postal_code} {city}
Tel: {phone}

Skontaktujemy się z Tobą wkrótce.

Pozdrawiamy,
Twoja Perfumka
''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass

        # Wyczyść koszyk
        cart.clear()

        return redirect('order_confirmation', pk=order.pk)

    return render(request, 'orders/checkout.html', {'cart': cart})


def order_confirmation(request, pk):
    order = Order.objects.get(pk=pk)
    return render(request, 'orders/confirmation.html', {'order': order})