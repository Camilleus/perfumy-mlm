from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


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
        # Sprawdź checkbox
        if not request.POST.get('accept_rules'):
            messages.error(request, 'Musisz zaakceptować warunki dotyczące zwrotu perfum.')
            return redirect('withdrawal_form')

        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        email = request.POST.get('email', '').strip()
        order_number = request.POST.get('order_number', '').strip()
        delivery_date = request.POST.get('delivery_date', '').strip()
        products = request.POST.get('products', '').strip()
        signature = request.POST.get('signature', '').strip()
        date = request.POST.get('date', '').strip()

        if not all([name, address, email, order_number, products, signature, date]):
            messages.error(request, 'Proszę wypełnić wszystkie wymagane pola.')
            return redirect('withdrawal_form')

        # Treść wiadomości dla sklepu
        subject_shop = f'Odstąpienie od umowy – zamówienie {order_number}'
        body_shop = f"""
Imię i nazwisko: {name}
Adres: {address}
E-mail: {email}
Numer zamówienia: {order_number}
Data otrzymania towaru: {delivery_date if delivery_date else 'nie podano'}
Produkty, od których odstępuję: {products}
Podpis: {signature}
Data wypełnienia formularza: {date}

Uwaga: Klient odstępuje od umowy zgodnie z art. 27 ustawy o prawach konsumenta.
        """

        # Treść potwierdzenia dla klienta
        subject_customer = f'Potwierdzenie otrzymania odstąpienia od umowy – zamówienie {order_number}'
        body_customer = f"""
Szanowny/a {name},

Dziękujemy za przesłanie formularza odstąpienia od umowy dla zamówienia nr {order_number}.

Przypominamy, że zgodnie z art. 38 ustawy o prawach konsumenta, odstąpienie od umowy nie przysługuje w przypadku perfum, jeśli oryginalne opakowanie zostało otwarte. Jeżeli produkt nie był testowany i opakowanie jest nienaruszone, prosimy o odesłanie go na adres:

Marcel Krzeja
ul. Kwiatowa 5
00-001 Warszawa

Zwrot środków nastąpi niezwłocznie, nie później niż w ciągu 14 dni od otrzymania towaru (lub dowodu jego odesłania).

W razie pytań jesteśmy do dyspozycji: sklep@przystanekperfumy.pl

Zespół Przystanek Perfumy
        """

        try:
            # Wysyłka do sklepu
            send_mail(
                subject_shop,
                body_shop,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],  # reklamacje@...
                fail_silently=False,
            )
            # Wysyłka potwierdzenia do klienta
            send_mail(
                subject_customer,
                body_customer,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Formularz odstąpienia został wysłany. Na Twój adres e-mail wysłaliśmy potwierdzenie.')
        except Exception as e:
            messages.error(request, 'Wystąpił błąd podczas wysyłania. Skontaktuj się bezpośrednio: sklep@przystanekperfumy.pl')
        return redirect('withdrawal_form')
    else:
        return redirect('withdrawal_form')