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
    """
    Dla cen 199.95 PLN i 249.95 PLN zwraca ładną wartość (np. 49.95 €).
    Dla innych kwot (np. sumy koszyka) zwraca dokładne przeliczenie (bez zaokrąglania do .95).
    """
    try:
        price = float(str(pln_price).replace(',', '.'))
        rate = curr.get('rate', 1.0)
        # Ceny jednostkowe
        if abs(price - 199.95) < 0.01:
            return curr['p199']
        if abs(price - 249.95) < 0.01:
            return curr['p249']
        # Wszystkie inne kwoty (sumy, iloczyny) – dokładne przeliczenie
        converted = price * rate
        # Sprawdzamy, czy waluta używa miejsc dziesiętnych
        uses_decimals = '.' in curr.get('p199', '')
        if uses_decimals:
            return f"{converted:.2f}"
        else:
            # Dla walut bez groszy (ISK, HUF, CZK itp.) zwracamy liczbę całkowitą
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