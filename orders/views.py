from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from products.models import Product
from .cart import Cart
from .models import Order, OrderItem
from django.http import JsonResponse

def cart_add(request, pk):
    cart = Cart(request)
    product = Product.objects.get(pk=pk)
    cart.add(product)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def cart_increase(request, pk):
    cart = Cart(request)
    product = Product.objects.get(pk=pk)
    cart.add(product, quantity=1)
    return redirect('cart_detail')


def cart_decrease(request, pk):
    cart = Cart(request)
    cart.decrease(pk)
    return redirect('cart_detail')


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

    discount = Decimal('0')
    referral_error = None

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        note = request.POST.get('note', '')
        referral_code = request.POST.get('referral_code', '').strip().upper()

        # Sprawdź kod polecenia
        referral_obj = None
        if referral_code:
            try:
                from sellers.models import Seller, Referral
                referrer = Seller.objects.get(referral_code=referral_code)
                discount = Decimal('20')
                referral_obj = referrer
            except Exception:
                referral_error = 'Nieprawidłowy kod polecenia.'
                discount = Decimal('0')

        total = max(Decimal(str(cart.get_total())) - discount, Decimal('0'))

        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal_code,
            note=note,
            total_amount=total,
            discount=discount,
        )

        for item in cart.get_items():
            product = Product.objects.get(pk=item['pk'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=item['price'],
            )

        # Przyznaj kredyt polecającemu
        if referral_obj:
            from sellers.models import Referral
            Referral.objects.create(
                referrer=referral_obj,
                referred_email=email,
                discount_used=True,
                credit_awarded=True,
            )
            referral_obj.credit += Decimal('20')
            referral_obj.save()

        # Email potwierdzający
        if email:
            try:
                send_mail(
                    subject=f'Potwierdzenie zamówienia #{order.pk} – Przystanek PsikPsik',
                    message=f'''Cześć {first_name or ""}!

Dziękujemy za zamówienie na Przystanku PsikPsik :D

Numer zamówienia: #{order.pk}
Łączna kwota: {order.total_amount} zł
{f"Zastosowana zniżka: -{discount} zł" if discount else ""}
Płatność: za pobraniem

Adres dostawy:
{first_name} {last_name}
{address}
{postal_code} {city}
Tel: {phone}

Skontaktujemy się z Tobą wkrótce.

Pozdrawiamy,
Przystanek PsikPsik
''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception:
                pass

        cart.clear()
        return redirect('order_confirmation', pk=order.pk)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'discount': discount,
        'referral_error': referral_error,
    })


def order_confirmation(request, pk):
    order = Order.objects.get(pk=pk)
    return render(request, 'orders/confirmation.html', {'order': order})    


def check_referral(request):
    code = request.GET.get('code', '').strip().upper()
    try:
        from sellers.models import Seller
        Seller.objects.get(referral_code=code)
        return JsonResponse({'valid': True})
    except Seller.DoesNotExist:
        return JsonResponse({'valid': False})
    
def my_orders(request):
    orders = None
    email_searched = None

    if request.user.is_authenticated:
        # Zalogowany – szuka po emailu z konta
        orders = Order.objects.filter(email=request.user.email).order_by('-created_at')
    elif request.method == 'POST':
        # Gość – wpisuje email
        email_searched = request.POST.get('email', '').strip()
        if email_searched:
            orders = Order.objects.filter(email=email_searched).order_by('-created_at')

    return render(request, 'orders/my_orders.html', {
        'orders': orders,
        'email_searched': email_searched,
    })