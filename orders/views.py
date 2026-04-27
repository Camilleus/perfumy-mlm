from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.conf import settings
from decimal import Decimal
from products.models import Product
from .cart import Cart
from .models import Order, OrderItem
from django.http import JsonResponse
import threading


def _send_email_html_async(subject, context, from_email, recipient_list, lang='pl'):
    try:
        # Sprawdź, czy język jest obsługiwany (idiotoodporność)
        available_langs = [code for code, name in settings.LANGUAGES]
        if lang not in available_langs:
            lang = settings.LANGUAGE_CODE   # domyślnie 'pl'
        
        translation.activate(lang)
        html_message = render_to_string('emails/order_confirmation.html', context)
        plain_message = f"Dziękujemy za zamówienie w Przystanku Perfumy!\n\nNumer zamówienia: #{context['order'].pk}\nKwota: {context['order'].total_amount} zł"
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=recipient_list,
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send(fail_silently=False)
    except Exception:
        # Nie przerywamy działania sklepu, e-mail po prostu nie zostanie wysłany – ale logujemy błąd (opcjonalnie)
        pass
    finally:
        translation.deactivate()


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
        shipping_method = request.POST.get('shipping_method', 'inpost')
        country = request.POST.get('country', '')

        # Sprawdź kod polecenia
        referral_obj = None
        if referral_code:
            try:
                from sellers.models import Seller
                referrer = Seller.objects.get(referral_code=referral_code)
                discount = Decimal('20')
                referral_obj = referrer
            except Exception:
                referral_error = 'Nieprawidłowy kod polecenia.'
                discount = Decimal('0')

        # Koszt wysyłki – maksymalnie prosto
        total_quantity = cart.get_total_quantity()
        shipping_method = request.POST.get('shipping_method', 'inpost')
        
        if shipping_method == 'international':
            shipping_cost = Decimal('250')
            shipping_method_name = 'Wysyłka zagraniczna'
        elif shipping_method == 'inpost':
            if total_quantity >= 3:
                shipping_cost = Decimal('0')
                shipping_method_name = 'InPost Kurier (darmowa)'
            else:
                shipping_cost = Decimal('30')
                shipping_method_name = 'InPost Kurier'
        else:
            shipping_cost = Decimal('40')
            shipping_method_name = 'GLS ekspres'

        total_products = Decimal(str(cart.get_total()))
        total = max(total_products - discount, Decimal('0')) + shipping_cost   # <-- tu dolicz shipping_cost

        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal_code,
            country=country,
            note=note,
            total_amount=total,                     # <-- to już zawiera wszystko, nie ruszaj
            discount=discount,
            shipping_method=shipping_method,        # 'international', 'inpost', 'gls'
            shipping_method_name=shipping_method_name,
            shipping_cost=shipping_cost,
            language=request.LANGUAGE_CODE,
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

        # Wyślij email
        if email:
            subject = f'Potwierdzenie zamówienia #{order.pk} – Przystanek Perfumy'
            order_items = OrderItem.objects.filter(order=order)

            total_products_val = order.total_amount + discount - shipping_cost
            shipping_display = "GRATIS" if shipping_cost == 0 else f"{shipping_cost:.2f} zł"
            shipping_color = "#2a6a2a" if shipping_cost == 0 else "#012b2a"

            context = {
                'order': order,
                'items': order_items,
                'discount': discount,
                'has_discount': bool(discount),
            }

            contact_emails = [e.strip() for e in settings.CONTACT_EMAIL.split(',')] if getattr(settings, 'CONTACT_EMAIL', None) else []
            recipients = list(set([email] + contact_emails))

            t = threading.Thread(
                target=_send_email_html_async,  
                args=(subject, context, settings.DEFAULT_FROM_EMAIL, recipients, order.language)
            )
            t.daemon = True
            t.start()

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
        orders = Order.objects.filter(email=request.user.email).order_by('-created_at')
    elif request.method == 'POST':
        email_searched = request.POST.get('email', '').strip()
        if email_searched:
            orders = Order.objects.filter(email=email_searched).order_by('-created_at')

    return render(request, 'orders/my_orders.html', {
        'orders': orders,
        'email_searched': email_searched,
    })


def cart_count(request):
    cart = Cart(request)
    return JsonResponse({'count': cart.count()})