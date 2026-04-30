#core/templatetags/currency_tags.py
import math
from django import template
from ..context_processors import CURRENCIES

register = template.Library()

def _round_to_95(value, uses_decimals):
    """Zaokrągla liczbę do najbliższej końcówki .95 (dla walut z ułamkami) lub 95 (dla walut bez ułamków)."""
    if uses_decimals:
        floor_val = math.floor(value)
        return floor_val + 0.95
    else:
        floor_hundreds = math.floor(value / 100) * 100
        return floor_hundreds + 95

@register.filter
def convert_price(pln_price, curr):
    try:
        price = float(str(pln_price).replace(',', '.'))
        rate = curr.get('rate', 1.0)
        if abs(price - 199.95) < 0.01:
            return curr['p199']
        if abs(price - 249.95) < 0.01:
            return curr['p249']
        if abs(price - 299.95) < 0.01:
            return curr.get('p299', curr['p249'])
        converted = price * rate
        uses_decimals = '.' in curr.get('p199', '')
        if uses_decimals:
            return f"{converted:.2f}"
        else:
            return str(int(round(converted)))
    except (ValueError, TypeError, KeyError):
        return pln_price

@register.filter
def convert_shipping(cost_pln, curr):
    try:
        cost = float(cost_pln)
        if cost == 0:
            return "0"
        rate = curr.get('rate', 1.0)
        converted = cost * rate
        uses_decimals = '.' in curr.get('p199', '')
        rounded = _round_to_95(converted, uses_decimals)
        if uses_decimals:
            return f"{rounded:.2f}"
        else:
            return str(int(rounded))
    except (ValueError, TypeError):
        return cost_pln

@register.filter
def add_prices(price1, price2):
    try:
        return f"{float(str(price1)) + float(str(price2)):.2f}"
    except (ValueError, TypeError):
        return price1
    

@register.filter
def cart_total_currency(cart, curr):
    """
    Zwraca łączną wartość koszyka w aktualnej walucie,
    poprzez zsumowanie przeliczonych cen jednostkowych.
    """
    try:
        total = 0
        for item in cart.get_items():
            price_pln = item['price']
            # Użyj logiki convert_price dla pojedynczego produktu
            if abs(price_pln - 199.95) < 0.01:
                converted_price = float(curr['p199'])
            elif abs(price_pln - 249.95) < 0.01:
                converted_price = float(curr['p249'])
            else:
                rate = curr.get('rate', 1.0)
                converted_price = price_pln * rate
            total += converted_price * item['quantity']
        # Zaokrąglenie do dwóch miejsc (dla walut z ułamkami) lub całości
        uses_decimals = '.' in curr.get('p199', '')
        if uses_decimals:
            return f"{total:.2f}"
        else:
            return str(int(round(total)))
    except Exception:
        return "0"
    
LANG_TO_FLAG = {
    'pl': 'pl',
    'cs': 'cz',  # czeski → flaga Czech
    'de': 'de',
    'es': 'es',
    'en': 'gb',  # angielski → flaga UK (lub 'us')
    'fr': 'fr',
    'hu': 'hu',
    'it': 'it',
    'nl': 'nl',
    'pt': 'pt',
    'ro': 'ro',
    'ru': 'ru',
    'sk': 'sk',
    'ua': 'ua',
}

@register.filter
def lang_flag(lang_code):
    return LANG_TO_FLAG.get(lang_code, lang_code)

@register.filter
def price_range_display(pln_price, curr):
    """Zamień granicę PLN na odpowiednik w aktualnej walucie."""
    try:
        price = float(str(pln_price).replace(',', '.'))
        # Mapowanie znanych granic
        known = {
            0: curr.get('p_min', '0'),
            199.95: curr.get('p199', '199.95'),
            200: curr.get('p200', str(int(float(curr.get('p199', 200)) + 1))),
            249.95: curr.get('p249', '249.95'),
            999: curr.get('p_max', '999'),
        }
        for pln_val, display in known.items():
            if abs(price - pln_val) < 1:
                return display
        # Nieznana wartość — przelicz proporcjonalnie
        divisor = curr.get('divisor', 1)
        raw = price / divisor
        return f"{int(raw)}"
    except:
        return pln_price