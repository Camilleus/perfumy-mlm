# core/context_processors.py
from orders.shipping import SHIPPING_METHODS
from django.utils.translation import get_language

CURRENCIES = {
    'PLN': {'name': 'Polski złoty',      'symbol': 'zł',  'rate': 1.0,     'p199': '199.95', 'p249': '249.95', 'p299': '299.95', 'p200': '200', 'p250': '250', 'p300': '300', 'shipping_pl': '30.00',  'shipping_intl': '249.95', 'discount': '20.00', 'sauvage_our': '199.95', 'sauvage_them': '415.50', 'chanel_our': '199.95', 'chanel_them': '709.00', 'armani_our': '199.95', 'armani_them': '499.00', 'ysl_our': '199.95', 'ysl_them': '459.50', 'versace_our': '199.95', 'versace_them': '365.00'},
    'EUR': {'name': 'Euro',              'symbol': '€',   'rate': 0.2498,  'p199': '49.95',  'p249': '59.95',  'p299': '74.95',  'p200': '50',  'p250': '60',  'p300': '75',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95',  'sauvage_our': '49.95',  'sauvage_them': '103.79', 'chanel_our': '49.95',  'chanel_them': '177.11', 'armani_our': '49.95',  'armani_them': '124.65', 'ysl_our': '49.95',  'ysl_them': '114.78', 'versace_our': '49.95',  'versace_them': '91.18'},
    'USD': {'name': 'Dolar amerykański', 'symbol': '$',   'rate': 0.2498,  'p199': '49.95',  'p249': '59.95',  'p299': '74.95',  'p200': '50',  'p250': '60',  'p300': '75',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95',  'sauvage_our': '49.95',  'sauvage_them': '103.79', 'chanel_our': '49.95',  'chanel_them': '177.11', 'armani_our': '49.95',  'armani_them': '124.65', 'ysl_our': '49.95',  'ysl_them': '114.78', 'versace_our': '49.95',  'versace_them': '91.18'},
    'GBP': {'name': 'Funt szterling',   'symbol': '£',   'rate': 0.2498,  'p199': '49.95',  'p249': '59.95',  'p299': '74.95',  'p200': '50',  'p250': '60',  'p300': '75',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95',  'sauvage_our': '49.95',  'sauvage_them': '103.79', 'chanel_our': '49.95',  'chanel_them': '177.11', 'armani_our': '49.95',  'armani_them': '124.65', 'ysl_our': '49.95',  'ysl_them': '114.78', 'versace_our': '49.95',  'versace_them': '91.18'},
    'CHF': {'name': 'Frank szwajcarski', 'symbol': 'Fr',  'rate': 0.2498,  'p199': '49.95',  'p249': '59.95',  'p299': '74.95',  'p200': '50',  'p250': '60',  'p300': '75',  'shipping_pl': '7.95',   'shipping_intl': '59.95',  'discount': '4.95',  'sauvage_our': '49.95',  'sauvage_them': '103.79', 'chanel_our': '49.95',  'chanel_them': '177.11', 'armani_our': '49.95',  'armani_them': '124.65', 'ysl_our': '49.95',  'ysl_them': '114.78', 'versace_our': '49.95',  'versace_them': '91.18'},
    'CAD': {'name': 'Dolar kanadyjski',  'symbol': 'C$',  'rate': 0.3499,  'p199': '69.95',  'p249': '79.95',  'p299': '99.95',  'p200': '70',  'p250': '80',  'p300': '100', 'shipping_pl': '9.95',   'shipping_intl': '79.95',  'discount': '6.95',  'sauvage_our': '69.96',  'sauvage_them': '145.38', 'chanel_our': '69.96',  'chanel_them': '248.08', 'armani_our': '69.96',  'armani_them': '174.60', 'ysl_our': '69.96',  'ysl_them': '160.78', 'versace_our': '69.96',  'versace_them': '127.71'},
    'NOK': {'name': 'Korona norweska',   'symbol': 'kr',  'rate': 3.0007,  'p199': '599.95', 'p249': '749.95', 'p299': '899.95', 'p200': '600', 'p250': '750', 'p300': '900', 'shipping_pl': '79.95',  'shipping_intl': '749.95', 'discount': '79.95', 'sauvage_our': '599.99', 'sauvage_them': '1246.79', 'chanel_our': '599.99', 'chanel_them': '2127.50', 'armani_our': '599.99', 'armani_them': '1497.35', 'ysl_our': '599.99', 'ysl_them': '1378.82', 'versace_our': '599.99', 'versace_them': '1095.26'},
    'SEK': {'name': 'Korona szwedzka',   'symbol': 'kr',  'rate': 3.0007,  'p199': '599.95', 'p249': '749.95', 'p299': '899.95', 'p200': '600', 'p250': '750', 'p300': '900', 'shipping_pl': '79.95',  'shipping_intl': '749.95', 'discount': '79.95', 'sauvage_our': '599.99', 'sauvage_them': '1246.79', 'chanel_our': '599.99', 'chanel_them': '2127.50', 'armani_our': '599.99', 'armani_them': '1497.35', 'ysl_our': '599.99', 'ysl_them': '1378.82', 'versace_our': '599.99', 'versace_them': '1095.26'},
    'DKK': {'name': 'Korona duńska',     'symbol': 'kr',  'rate': 2.0003,  'p199': '399.95', 'p249': '449.95', 'p299': '549.95', 'p200': '400', 'p250': '450', 'p300': '550', 'shipping_pl': '49.95',  'shipping_intl': '449.95', 'discount': '39.95', 'sauvage_our': '399.96', 'sauvage_them': '831.12', 'chanel_our': '399.96', 'chanel_them': '1418.21', 'armani_our': '399.96', 'armani_them': '998.15', 'ysl_our': '399.96', 'ysl_them': '919.14', 'versace_our': '399.96', 'versace_them': '730.11'},
    'ISK': {'name': 'Korona islandzka',  'symbol': 'kr',  'rate': 40.0,    'p199': '7995',   'p249': '8995',   'p299': '10995',  'p200': '8000','p250': '9000','p300': '11000','shipping_pl': '995',    'shipping_intl': '8995',   'discount': '995',   'sauvage_our': '7998',   'sauvage_them': '16620',  'chanel_our': '7998',   'chanel_them': '28360',  'armani_our': '7998',   'armani_them': '19960',  'ysl_our': '7998',   'ysl_them': '18380',  'versace_our': '7998',   'versace_them': '14600'},
    'CZK': {'name': 'Korona czeska',     'symbol': 'Kč',  'rate': 5.7264,  'p199': '1145',   'p249': '1445',   'p299': '1745',   'p200': '1150','p250': '1450','p300': '1750', 'shipping_pl': '145',    'shipping_intl': '1445',   'discount': '145',   'sauvage_our': '1145',   'sauvage_them': '2379',   'chanel_our': '1145',   'chanel_them': '4060',   'armani_our': '1145',   'armani_them': '2857',   'ysl_our': '1145',   'ysl_them': '2631',   'versace_our': '1145',   'versace_them': '2090'},
    'HUF': {'name': 'Forint węgierski',  'symbol': 'Ft',  'rate': 85.0,    'p199': '16995',  'p249': '21995',  'p299': '26995',  'p200': '17000','p250': '22000','p300': '27000','shipping_pl': '1995',  'shipping_intl': '21995',  'discount': '1995',  'sauvage_our': '16996',  'sauvage_them': '35318',  'chanel_our': '16996',  'chanel_them': '60265',  'armani_our': '16996',  'armani_them': '42415',  'ysl_our': '16996',  'ysl_them': '39058',  'versace_our': '16996',  'versace_them': '31025'},
    'RON': {'name': 'Lej rumuński',      'symbol': 'lei', 'rate': 1.2503,  'p199': '249.95', 'p249': '299.95', 'p299': '374.95', 'p200': '250', 'p250': '300', 'p300': '375', 'shipping_pl': '29.95',  'shipping_intl': '299.95', 'discount': '29.95', 'sauvage_our': '250.00', 'sauvage_them': '519.50', 'chanel_our': '250.00', 'chanel_them': '886.46', 'armani_our': '250.00', 'armani_them': '623.90', 'ysl_our': '250.00', 'ysl_them': '574.51', 'versace_our': '250.00', 'versace_them': '456.36'},
    'UAH': {'name': 'Hrywna ukraińska',  'symbol': '₴',   'rate': 12.478,  'p199': '2495',   'p249': '2995',   'p299': '3695',   'p200': '2500','p250': '3000','p300': '3700', 'shipping_pl': '295',    'shipping_intl': '2995',   'discount': '295',   'sauvage_our': '2495',   'sauvage_them': '5185',   'chanel_our': '2495',   'chanel_them': '8847',   'armani_our': '2495',   'armani_them': '6227',   'ysl_our': '2495',   'ysl_them': '5734',   'versace_our': '2495',   'versace_them': '4554'},
    'TRY': {'name': 'Lira turecka',      'symbol': '₺',   'rate': 12.478,  'p199': '2495',   'p249': '2995',   'p299': '3695',   'p200': '2500','p250': '3000','p300': '3700', 'shipping_pl': '295',    'shipping_intl': '2995',   'discount': '295',   'sauvage_our': '2495',   'sauvage_them': '5185',   'chanel_our': '2495',   'chanel_them': '8847',   'armani_our': '2495',   'armani_them': '6227',   'ysl_our': '2495',   'ysl_them': '5734',   'versace_our': '2495',   'versace_them': '4554'},
    'RUB': {'name': 'Rubel rosyjski',    'symbol': '₽',   'rate': 27.482,  'p199': '5495',   'p249': '6495',   'p299': '7995',   'p200': '5500','p250': '6500','p300': '8000', 'shipping_pl': '595',    'shipping_intl': '6495',   'discount': '595',   'sauvage_our': '5495',   'sauvage_them': '11419',  'chanel_our': '5495',   'chanel_them': '19485',  'armani_our': '5495',   'armani_them': '13714',  'ysl_our': '5495',   'ysl_them': '12628',  'versace_our': '5495',   'versace_them': '10031'},
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