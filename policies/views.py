from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect


class RegulaminView(TemplateView):
    template_name = 'policies/regulamin.html'

class PrivacyPolicyView(TemplateView):
    template_name = 'policies/privacy_policy.html'

class ReturnsPolicyView(TemplateView):
    template_name = 'policies/returns_policy.html'

class OdrView(TemplateView):
    template_name = 'policies/odr.html'

class OmnibusView(TemplateView):
    template_name = 'policies/omnibus.html'

class ContactView(TemplateView):
    template_name = 'policies/contact.html'

def contact_submit(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        order_number = request.POST.get('order_number', '')
        message = request.POST.get('message')

        if not name or not email or not message:
            messages.error(request, 'Proszę wypełnić wszystkie wymagane pola.')
            return redirect('contact')

        subject = f'Wiadomość ze sklepu od {name}'
        body = f"""
Imię: {name}
Email: {email}
Numer zamówienia: {order_number if order_number else 'nie podano'}

Wiadomość:
{message}
        """
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                      [settings.CONTACT_EMAIL], fail_silently=False)
            messages.success(request, 'Twoja wiadomość została wysłana. Odpowiemy wkrótce.')
        except Exception:
            messages.error(request, 'Wystąpił błąd. Spróbuj ponownie później.')
        return redirect('contact')
    return redirect('contact')

def withdrawal_submit(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        email = request.POST.get('email')
        order_number = request.POST.get('order_number')
        delivery_date = request.POST.get('delivery_date')
        products = request.POST.get('products')
        signature = request.POST.get('signature')
        date = request.POST.get('date')

        if not name or not email or not order_number:
            messages.error(request, 'Proszę wypełnić wymagane pola (imię, e-mail, numer zamówienia).')
            return redirect('withdrawal_form')

        # Przygotuj treść e-maila
        subject = f'Odstąpienie od umowy - zamówienie {order_number}'
        body = f"""
Imię i nazwisko: {name}
Adres: {address}
E-mail: {email}
Numer zamówienia: {order_number}
Data otrzymania towaru: {delivery_date if delivery_date else 'nie podano'}
Produkty: {products}
Podpis: {signature}
Data wypełnienia: {date}

Uwaga: Klient odstępuje od umowy zgodnie z art. 27 ustawy o prawach konsumenta.
        """
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],  # lub osobny adres do reklamacji
                fail_silently=False,
            )
            messages.success(request, 'Formularz odstąpienia został wysłany. Otrzymasz potwierdzenie wkrótce.')
        except Exception:
            messages.error(request, 'Wystąpił błąd podczas wysyłania formularza. Skontaktuj się bezpośrednio przez e-mail.')
        return redirect('withdrawal_form')
    else:
        return redirect('withdrawal_form')