from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from sellers.models import Seller

@login_required
def seller_panel(request):
    try:
        seller = request.user.seller
    except ObjectDoesNotExist:
        return render(request, 'sellers/no_access.html')

    if not seller.is_approved:
        return render(request, 'sellers/pending.html')

    sales = seller.sales.all().order_by('-sale_date')
    commissions = seller.commissions.all().order_by('-created_at')
    total_sales = sum(s.total_amount for s in sales)
    total_commissions = sum(c.amount for c in commissions)
    referrals = seller.referrals.all()

    return render(request, 'sellers/panel.html', {
        'seller': seller,
        'sales': sales,
        'commissions': commissions,
        'total_sales': total_sales,
        'total_commissions': total_commissions,
        'referrals': referrals,
    })
    

class SellerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    sponsor_code = forms.CharField(max_length=150, required=False, label='Kod polecającego (opcjonalnie)')

def register(request):
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            sponsor = None
            sponsor_code = form.cleaned_data.get('sponsor_code')
            if sponsor_code:
                try:
                    sponsor_user = User.objects.get(username=sponsor_code)
                    sponsor = sponsor_user.seller
                except (User.DoesNotExist, ObjectDoesNotExist):
                    pass
            Seller.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', ''),
                sponsor=sponsor,
            )
            login(request, user)
            return redirect('seller_panel')
    else:
        form = SellerRegistrationForm()
    return render(request, 'sellers/register.html', {'form': form})