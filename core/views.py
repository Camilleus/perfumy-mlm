from django.shortcuts import redirect
from core.context_processors import CURRENCIES

def set_currency(request):
    code = request.POST.get('currency', 'PLN')
    if code in CURRENCIES:
        request.session['currency'] = code
    return redirect(request.POST.get('next', '/'))