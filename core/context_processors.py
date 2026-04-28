CURRENCIES = {
    'PLN': {'name': 'Polski złoty',        'symbol': 'zł',  'p199': '199.95', 'p249': '249.95', 'shipping': '30.00'},
    'EUR': {'name': 'Euro',                'symbol': '€',   'p199': '49.95',  'p249': '59.95',  'shipping': '59.95'},
    'USD': {'name': 'Dolar amerykański',   'symbol': '$',   'p199': '49.95',  'p249': '59.95',  'shipping': '59.95'},
    'GBP': {'name': 'Funt szterling',      'symbol': '£',   'p199': '49.95',  'p249': '59.95',  'shipping': '59.95'},
    'CHF': {'name': 'Frank szwajcarski',   'symbol': 'Fr',  'p199': '49.95',  'p249': '59.95',  'shipping': '59.95'},
    'CAD': {'name': 'Dolar kanadyjski',    'symbol': 'C$',  'p199': '69.95',  'p249': '79.95',  'shipping': '79.95'},
    'NOK': {'name': 'Korona norweska',     'symbol': 'kr',  'p199': '599.95', 'p249': '749.95', 'shipping': '749.95'},
    'SEK': {'name': 'Korona szwedzka',     'symbol': 'kr',  'p199': '599.95', 'p249': '749.95', 'shipping': '749.95'},
    'DKK': {'name': 'Korona duńska',       'symbol': 'kr',  'p199': '399.95', 'p249': '449.95', 'shipping': '449.95'},
    'ISK': {'name': 'Korona islandzka',    'symbol': 'kr',  'p199': '7995',   'p249': '8995',   'shipping': '8995'},
    'CZK': {'name': 'Korona czeska',       'symbol': 'Kč',  'p199': '1145',   'p249': '1445',   'shipping': '1445'},
    'HUF': {'name': 'Forint węgierski',    'symbol': 'Ft',  'p199': '16995',  'p249': '21995',  'shipping': '21995'},
    'RON': {'name': 'Lej rumuński',        'symbol': 'lei', 'p199': '249.95', 'p249': '299.95', 'shipping': '299.95'},
    'UAH': {'name': 'Hrywna ukraińska',    'symbol': '₴',   'p199': '2495',   'p249': '2995',   'shipping': '2995'},
    'TRY': {'name': 'Lira turecka',        'symbol': '₺',   'p199': '2495',   'p249': '2995',   'shipping': '2995'},
    'RUB': {'name': 'Rubel rosyjski',      'symbol': '₽',   'p199': '5495',   'p249': '6495',   'shipping': '6495'},
}

LANG_TO_CURRENCY = {
    'pl': 'PLN',
    'es': 'EUR',
}

def currency(request):
    lang = getattr(request, 'LANGUAGE_CODE', 'pl')
    default = LANG_TO_CURRENCY.get(lang, 'PLN')
    code = request.session.get('currency', default)
    if code not in CURRENCIES:
        code = 'PLN'
    curr = CURRENCIES[code]
    return {
        'CURRENCY_CODE': code,
        'CURRENCY_SYMBOL': curr['symbol'],
        'ALL_CURRENCIES': CURRENCIES,
        'CURR': curr,
    }