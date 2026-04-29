# orders/views.py
from core.context_processors import CURRENCIES
from orders.shipping import SHIPPING_METHODS as SHIPPING_CONFIG
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


def _calc_total_currency(cart, curr):
    """Pomocnicza – liczy sumę koszyka w walucie klienta."""
    rate = Decimal(str(float(curr['p199']) / 199.95))
    total = Decimal('0')
    for item in cart.get_items():
        price_pln = Decimal(str(item['price']))
        if abs(price_pln - Decimal('199.95')) < Decimal('0.01'):
            conv = Decimal(curr['p199'])
        elif abs(price_pln - Decimal('249.95')) < Decimal('0.01'):
            conv = Decimal(curr['p249'])
        else:
            conv = price_pln * rate
        total += conv * item['quantity']
    return total


def _fmt(val, curr):
    """Pomocnicza – formatuje liczbę do stringa w zależności od waluty."""
    uses_decimals = '.' in curr.get('p199', '')
    if uses_decimals:
        return f"{val:.2f}"
    return str(int(round(val)))


def _send_email_html_async(subject, context, from_email, recipient_list, lang='pl', plain_message_override=None):
    try:
        available_langs = [code for code, name in settings.LANGUAGES]
        if lang not in available_langs:
            lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        html_message = render_to_string('emails/order_confirmation.html', context)
        plain_message = plain_message_override or f"Dziękujemy za zamówienie!\n\n#{context['order'].pk}\nKwota: {context['order'].total_amount_currency} {context['order'].currency_symbol}"
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=recipient_list,
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send(fail_silently=False)
    except Exception:
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
    currency_code = request.session.get('currency', 'PLN')
    curr = CURRENCIES.get(currency_code, CURRENCIES['PLN']).copy()
    total_currency = _calc_total_currency(cart, curr)
    total_currency_str = _fmt(total_currency, curr)
    total_quantity = cart.get_total_quantity()
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'cart_total_currency': total_currency_str,
        'total_quantity': total_quantity,                # <-- dodane
        'currency_symbol': curr['symbol'],
    })


def checkout(request):
    cart = Cart(request)
    if cart.count() == 0:
        return redirect('cart_detail')

    currency_code = request.session.get('currency', 'PLN')
    curr = CURRENCIES.get(currency_code, CURRENCIES['PLN']).copy()
    rate = Decimal(str(float(curr['p199']) / 199.95))
    curr['rate'] = rate

    discount = Decimal('0')
    referral_error = None

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        postal_code = request.POST.get('postal_code', '')
        note = request.POST.get('note', '')
        referral_code = request.POST.get('referral_code', '').strip().upper()
        shipping_method = request.POST.get('shipping_method', 'inpost')
        country = request.POST.get('country', '')

        # Kod polecenia
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

        total_quantity = cart.get_total_quantity()
        country_lower = country.strip().lower()
        polish_names = ['polska', 'poland', 'pl', 'polonia', 'lechistan', 'lenkija', 'polen', 'rp', 'lechia', '']
        is_poland = country_lower in polish_names

        # Koszt wysyłki w PLN i walucie
        if not is_poland:
            shipping_method = 'international'
            shipping_cost = Decimal('249.95')
            shipping_method_name = 'Wysyłka zagraniczna'
            shipping_cost_currency = Decimal(curr['shipping_intl'])
        else:
            pl_methods = {m['id']: m for m in SHIPPING_CONFIG['pl']}
            method_data = pl_methods.get(shipping_method, pl_methods['inpost'])
            free_above = method_data.get('free_above_qty', None)
            if free_above and total_quantity >= free_above:
                shipping_cost = Decimal('0')
                shipping_cost_currency = Decimal('0')
                shipping_method_name = f"{method_data['name']} (darmowa)"
            else:
                shipping_cost = Decimal(str(method_data['cost_pln']))
                shipping_cost_currency = Decimal(curr['shipping_pl'])
                shipping_method_name = method_data['name']

        # Sumy
        total_products_pln = Decimal(str(cart.get_total()))
        total_pln = max(total_products_pln - discount, Decimal('0')) + shipping_cost

        # Suma w walucie
        total_currency = _calc_total_currency(cart, curr)
        discount_currency = Decimal(curr['discount']) if discount > 0 else Decimal('0')
        total_amount_currency = total_currency - discount_currency + shipping_cost_currency

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
            total_amount=total_pln,
            discount=discount,
            shipping_method=shipping_method,
            shipping_method_name=shipping_method_name,
            shipping_cost=shipping_cost,
            language=request.LANGUAGE_CODE,
            currency=currency_code,
            currency_symbol=curr['symbol'],
            total_amount_currency=total_amount_currency,
            shipping_cost_currency=shipping_cost_currency,
        )

        for item in cart.get_items():
            product = Product.objects.get(pk=item['pk'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=item['price'],
            )

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

        if email:
            subject = f'Potwierdzenie zamówienia #{order.pk} – Przystanek Perfumy'
            order_items = OrderItem.objects.filter(order=order)
            context = {
                'order': order,
                'items': order_items,
                'discount': discount,
                'discount_currency': discount_currency,
                'has_discount': bool(discount),
                'curr': curr,
                'currency_symbol': curr['symbol'],
            }
            plain_message = f"Dziękujemy za zamówienie!\n\nNumer: #{order.pk}\nKwota: {_fmt(total_amount_currency, curr)} {curr['symbol']}"
            contact_emails = [e.strip() for e in settings.CONTACT_EMAIL.split(',')] if getattr(settings, 'CONTACT_EMAIL', None) else []
            recipients = list(set([email] + contact_emails))
            t = threading.Thread(
                target=_send_email_html_async,
                args=(subject, context, settings.DEFAULT_FROM_EMAIL, recipients, order.language, plain_message)
            )
            t.daemon = True
            t.start()

        cart.clear()
        return redirect('order_confirmation', pk=order.pk)

    # GET
    total_currency = _calc_total_currency(cart, curr)
    cart_total_currency = _fmt(total_currency, curr)
    max_shipping_display = curr['shipping_intl']

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'discount': discount,
        'referral_error': referral_error,
        'cart_total_currency': cart_total_currency,
        'CURRENCY_SYMBOL': curr['symbol'],
        'CURR': curr,
        'max_shipping_display': max_shipping_display,
        'SHIPPING_METHODS': SHIPPING_CONFIG,
        'total_quantity': cart.get_total_quantity(),
    })


def order_confirmation(request, pk):
    order = Order.objects.get(pk=pk)
    curr = CURRENCIES.get(order.currency, CURRENCIES['PLN'])
    return render(request, 'orders/confirmation.html', {
        'order': order,
        'CURR': curr,
        'CURRENCY_SYMBOL': order.currency_symbol,
    })


def calculate_checkout(request):
    """AJAX endpoint – liczy koszty w Pythonie, zwraca JSON."""
    cart = Cart(request)
    currency_code = request.session.get('currency', 'PLN')
    curr = CURRENCIES.get(currency_code, CURRENCIES['PLN']).copy()
    rate = Decimal(str(float(curr['p199']) / 199.95))
    curr['rate'] = rate

    country = request.GET.get('country', '').strip().lower()
    shipping_method_id = request.GET.get('shipping_method', 'inpost')
    discount_applied = request.GET.get('discount', 'false') == 'true'

    polish_names = ['polska', 'poland', 'pl', 'polonia', 'lechistan', 'lenkija', 'polen', 'rp', 'lechia', '']
    is_poland = country in polish_names
    total_quantity = cart.get_total_quantity()

    # Wysyłka
    if not is_poland:
        shipping_method_id = 'international'
        shipping_currency = Decimal(curr['shipping_intl'])
    else:
        pl_methods = {m['id']: m for m in SHIPPING_CONFIG['pl']}
        method = pl_methods.get(shipping_method_id, pl_methods['inpost'])
        free_above = method.get('free_above_qty', None)
        if free_above and total_quantity >= free_above:
            shipping_currency = Decimal('0')
        else:
            shipping_currency = Decimal(curr['shipping_pl'])

    # Rabat
    discount_currency = Decimal(curr['discount']) if discount_applied else Decimal('0')

    # Suma produktów
    total_currency = _calc_total_currency(cart, curr)
    total_final = total_currency - discount_currency + shipping_currency

    return JsonResponse({
        'is_poland': is_poland,
        'shipping_method': shipping_method_id,
        'products_total': _fmt(total_currency, curr),
        'shipping': _fmt(shipping_currency, curr),
        'discount': _fmt(discount_currency, curr),
        'total': _fmt(total_final, curr),
        'symbol': curr['symbol'],
    })


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