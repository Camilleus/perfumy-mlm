from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from decimal import Decimal
from products.models import Product
from .cart import Cart
from .models import Order, OrderItem
from django.http import JsonResponse
import threading


def _build_email_html(order, items, discount, shipping_method_name, shipping_cost):
    items_rows = ""
    for item in items:
        subtotal = item.price * item.quantity
        items_rows += f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #e8dfc0;font-size:14px;color:#012b2a;">
            <strong>{item.product.name}</strong><br>
            <span style="font-size:12px;color:#8a7a3a;">100 ml &middot; szt. {item.quantity}</span>
          </td>
          <td style="padding:10px 14px;border-bottom:1px solid #e8dfc0;font-size:14px;color:#012b2a;text-align:right;white-space:nowrap;">
            {subtotal:.2f} zł
          </td>
        </tr>"""

    discount_row = ""
    if discount:
        discount_row = f'<tr><td style="padding:4px 0;font-size:13px;color:#8a2020;">Rabat (kod polecenia)</td><td style="padding:4px 0;font-size:13px;color:#8a2020;text-align:right;">-{discount:.2f} zł</td></tr>'

    shipping_display = "GRATIS" if shipping_cost == 0 else f"{shipping_cost:.2f} zł"
    shipping_color = "#2a6a2a" if shipping_cost == 0 else "#012b2a"
    total_products = order.total_amount + discount - shipping_cost

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f0e8;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:2rem;">
<table width="560" cellpadding="0" cellspacing="0" style="background:#FFFAE2;border:1px solid #c9a227;">

  <tr><td style="background:#012b2a;padding:2rem;text-align:center;border-bottom:3px solid #D4AF37;">
    <div style="font-size:11px;letter-spacing:3px;color:#D4AF37;text-transform:uppercase;">Przystanek</div>
    <div style="font-size:26px;font-weight:700;color:#D4AF37;letter-spacing:1px;">Perfumy</div>
  </td></tr>

  <tr><td style="padding:2rem 2rem 1rem;text-align:center;border-bottom:1px solid #e8dfc0;">
    <div style="font-size:11px;letter-spacing:2px;color:#8a7a3a;text-transform:uppercase;">Potwierdzenie zamówienia</div>
    <div style="font-size:22px;color:#012b2a;font-weight:700;margin-top:0.5rem;">Dziękujemy, {order.first_name}!</div>
    <p style="color:#4a4030;font-size:14px;line-height:1.7;">Twoje zamówienie <strong style="color:#012b2a;">#{order.pk}</strong> zostało przyjęte i wkrótce trafi w drogę.</p>
  </td></tr>

  <tr><td style="padding:1.5rem 2rem 0.5rem;">
    <div style="font-size:11px;letter-spacing:2px;color:#8a7a3a;text-transform:uppercase;margin-bottom:1rem;">Zamówione produkty</div>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8dfc0;">
      {items_rows}
    </table>
  </td></tr>

  <tr><td style="padding:1rem 2rem 1.5rem;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0e0;padding:1rem;border-radius:3px;">
      <tr><td style="padding:4px 0;font-size:13px;color:#4a4030;">Produkty</td><td style="padding:4px 0;font-size:13px;color:#4a4030;text-align:right;">{total_products:.2f} zł</td></tr>
      <tr><td style="padding:4px 0;font-size:13px;color:#4a4030;">Dostawa ({shipping_method_name})</td><td style="padding:4px 0;font-size:13px;color:{shipping_color};font-weight:600;text-align:right;">{shipping_display}</td></tr>
      {discount_row}
      <tr><td colspan="2" style="padding:8px 0 4px;"><hr style="border:none;border-top:1px solid #D4AF37;opacity:0.5;"></td></tr>
      <tr><td style="font-size:16px;font-weight:700;color:#012b2a;">Razem do zapłaty</td><td style="font-size:16px;font-weight:700;color:#012b2a;text-align:right;">{order.total_amount:.2f} zł</td></tr>
      <tr><td colspan="2" style="font-size:12px;color:#8a7a3a;text-align:right;padding-top:4px;">płatność za pobraniem</td></tr>
    </table>
  </td></tr>

  <tr><td style="padding:0 2rem 1.5rem;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="48%" style="background:#f5f0e0;padding:0.9rem 1rem;vertical-align:top;">
        <div style="font-size:10px;letter-spacing:2px;color:#8a7a3a;text-transform:uppercase;margin-bottom:6px;">Dostawa</div>
        <div style="font-size:13px;color:#012b2a;">{order.first_name} {order.last_name}</div>
        <div style="font-size:13px;color:#4a4030;">{order.address}</div>
        <div style="font-size:13px;color:#4a4030;">{order.postal_code} {order.city}</div>
        <div style="font-size:13px;color:#4a4030;">tel. {order.phone}</div>
      </td>
      <td width="4%"></td>
      <td width="48%" style="background:#f5f0e0;padding:0.9rem 1rem;vertical-align:top;">
        <div style="font-size:10px;letter-spacing:2px;color:#8a7a3a;text-transform:uppercase;margin-bottom:6px;">Wysyłka</div>
        <div style="font-size:13px;color:#012b2a;font-weight:600;">{shipping_method_name}</div>
        <div style="font-size:12px;color:#4a4030;margin-top:4px;">Zamówienie przetworzymy w ciągu 1–2 dni roboczych.</div>
      </td>
    </tr></table>
  </td></tr>

  <tr><td style="background:#012b2a;padding:1.25rem 2rem;text-align:center;border-top:2px solid #D4AF37;">
    <p style="color:#D4AF37;font-size:13px;margin:0 0 0.5rem;font-style:italic;">&ldquo;Każda perfuma to historia — cieszymy się, że piszesz ją z nami.&rdquo;</p>
    <p style="color:#8a9a8a;font-size:11px;margin:0;letter-spacing:1px;">przystanekperfumy.pl &middot; kontakt@przystanekperfumy.pl</p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""
    return html


def _send_email_html_async(subject, html_message, from_email, recipient_list):
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Dziękujemy za zamówienie w Przystanku Perfumy!",
            from_email=from_email,
            to=recipient_list,
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send(fail_silently=False)
    except Exception:
        pass


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

        # Koszt wysyłki
        total_quantity = cart.get_total_quantity()
        if shipping_method == 'inpost':
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
        total = max(total_products - discount, Decimal('0')) + shipping_cost

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
            shipping_method=shipping_method,
            shipping_cost=shipping_cost,
            shipping_method_name=shipping_method_name,
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
            html_message = _build_email_html(
                order=order,
                items=order_items,
                discount=discount,
                shipping_method_name=shipping_method_name,
                shipping_cost=shipping_cost,
            )
            contact_emails = [e.strip() for e in settings.CONTACT_EMAIL.split(',')] if getattr(settings, 'CONTACT_EMAIL', None) else []
            recipients = list(set([email] + contact_emails))  # bez duplikatów

            t = threading.Thread(
                target=_send_email_html_async,
                args=(subject, html_message, settings.DEFAULT_FROM_EMAIL, recipients)
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