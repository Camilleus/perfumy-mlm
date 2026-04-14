from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from sellers.models import Seller, Referral


@login_required
def seller_panel(request):
    try:
        seller = request.user.seller
    except ObjectDoesNotExist:
        return render(request, 'sellers/no_access.html')

    referrals = seller.referrals.all().order_by('-created_at')
    referral_count = referrals.count()
    successful_referrals = referrals.filter(credit_awarded=True).count()

    return render(request, 'sellers/panel.html', {
        'seller': seller,
        'referrals': referrals,
        'referral_count': referral_count,
        'successful_referrals': successful_referrals,
    })


class SellerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False, label='Telefon (opcjonalnie)')
    referral_code = forms.CharField(max_length=20, required=False, label='Kod polecającego (opcjonalnie)')

    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'phone', 'password1', 'password2']


def register(request, referral_code=None):
    # 1. Obsługa kodu z URL (np. /rejestracja/CAMIL-CD3O/)
    initial_code = referral_code or request.GET.get('ref', '')
    
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        submitted_code = request.POST.get('referral_code', '')

        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()

            seller = Seller.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', ''),
            )

            # Kod do wykorzystania: najpierw z formularza, potem z URL
            used_code = submitted_code or initial_code
            if used_code:
                try:
                    referrer = Seller.objects.get(referral_code=used_code.upper())
                    Referral.objects.create(
                        referrer=referrer,
                        referred_email=user.email,
                    )
                    # Zapisz kod w sesji – zniżka przy pierwszym zamówieniu
                    request.session['referral_code'] = used_code.upper()
                except Seller.DoesNotExist:
                    pass

            login(request, user)
            return redirect('seller_panel')
    else:
        # Wypełnij pole referral_code wartością z URL (jeśli istnieje)
        initial = {'referral_code': initial_code} if initial_code else {}
        form = SellerRegistrationForm(initial=initial)

    return render(request, 'sellers/register.html', {
        'form': form,
        'referral_code': initial_code,
    })