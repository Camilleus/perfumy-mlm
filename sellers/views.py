from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

@login_required
def seller_panel(request):
    try:
        seller = request.user.seller
    except ObjectDoesNotExist:
        return render(request, 'sellers/no_access.html')

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