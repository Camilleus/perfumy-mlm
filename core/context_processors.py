# core/context_processors.py
from orders.shipping import SHIPPING_METHODS
from django.utils.translation import get_language

CURRENCIES = {
    'PLN': {'name': 'Polski złoty',      'symbol': 'zł',  'p199': '199.95', 'p249': '249.95', 'shipping_pl': '30.00',  'shipping_intl': '249.95', 'discount': '20.00'},
    'EUR': {'name': 'Euro',              'symbol': '€',   'p199': '49.95',  'p249': '59.95',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95'},
    'USD': {'name': 'Dolar amerykański', 'symbol': '$',   'p199': '49.95',  'p249': '59.95',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95'},
    'GBP': {'name': 'Funt szterling',   'symbol': '£',   'p199': '49.95',  'p249': '59.95',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95'},
    'CHF': {'name': 'Frank szwajcarski','symbol': 'Fr',  'p199': '49.95',  'p249': '59.95',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95'},
    'CAD': {'name': 'Dolar kanadyjski', 'symbol': 'C$',  'p199': '69.95',  'p249': '79.95',  'shipping_pl': '9.95',   'shipping_intl': '79.95',  'discount': '6.95'},
    'NOK': {'name': 'Korona norweska',  'symbol': 'kr',  'p199': '599.95', 'p249': '749.95', 'shipping_pl': '79.95',  'shipping_intl': '749.95', 'discount': '79.95'},
    'SEK': {'name': 'Korona szwedzka',  'symbol': 'kr',  'p199': '599.95', 'p249': '749.95', 'shipping_pl': '79.95',  'shipping_intl': '749.95', 'discount': '79.95'},
    'DKK': {'name': 'Korona duńska',   'symbol': 'kr',  'p199': '399.95', 'p249': '449.95', 'shipping_pl': '49.95',  'shipping_intl': '449.95', 'discount': '39.95'},
    'ISK': {'name': 'Korona islandzka','symbol': 'kr',  'p199': '7995',   'p249': '8995',   'shipping_pl': '995',    'shipping_intl': '8995',   'discount': '995'},
    'CZK': {'name': 'Korona czeska',   'symbol': 'Kč',  'p199': '1145',   'p249': '1445',   'shipping_pl': '145',    'shipping_intl': '1445',   'discount': '145'},
    'HUF': {'name': 'Forint węgierski','symbol': 'Ft',  'p199': '16995',  'p249': '21995',  'shipping_pl': '1995',   'shipping_intl': '21995',  'discount': '1995'},
    'RON': {'name': 'Lej rumuński',    'symbol': 'lei', 'p199': '249.95', 'p249': '299.95', 'shipping_pl': '29.95',  'shipping_intl': '299.95', 'discount': '29.95'},
    'UAH': {'name': 'Hrywna ukraińska','symbol': '₴',   'p199': '2495',   'p249': '2995',   'shipping_pl': '295',    'shipping_intl': '2995',   'discount': '295'},
    'TRY': {'name': 'Lira turecka',    'symbol': '₺',   'p199': '2495',   'p249': '2995',   'shipping_pl': '295',    'shipping_intl': '2995',   'discount': '295'},
    'RUB': {'name': 'Rubel rosyjski',  'symbol': '₽',   'p199': '5495',   'p249': '6495',   'shipping_pl': '595',    'shipping_intl': '6495',   'discount': '595'},
}

LANG_TO_CURRENCY = {
    'pl': 'PLN',
    'en': 'GBP',   # lub 'USD', ale 'GBP' dla UK
    'es': 'EUR',
    'de': 'EUR',
    'fr': 'EUR',
    'it': 'EUR',
    'nl': 'EUR',
    'pt': 'EUR',
    'cs': 'CZK',
    'hu': 'HUF',
    'ro': 'RON',
    'ru': 'RUB',
    'ua': 'UAH',
    'sk': 'EUR',   # Słowacja (euro)
}

def currency(request):
    lang = get_language()
    default = LANG_TO_CURRENCY.get(lang, 'PLN')
    code = request.session.get('currency', default)
    if code not in CURRENCIES:
        code = 'PLN'
    curr = CURRENCIES[code].copy()
    # Współczynnik przeliczenia (kurs) względem PLN
    rate = float(curr['p199']) / 199.95
    curr['rate'] = rate

    # Przygotuj słownik kursów dla wszystkich walut (potrzebny w JS)
    exchange_rates = {}
    for cur_code, cur_data in CURRENCIES.items():
        exchange_rates[cur_code] = float(cur_data['p199']) / 199.95

    return {
        'CURRENCY_CODE': code,
        'CURRENCY_SYMBOL': curr['symbol'],
        'ALL_CURRENCIES': CURRENCIES,
        'CURR': curr,
        'SHIPPING_METHODS': SHIPPING_METHODS,
        'EXCHANGE_RATES': exchange_rates,   # dla JS
    }