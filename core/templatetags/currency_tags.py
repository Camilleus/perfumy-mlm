import math
from django import template

register = template.Library()

@register.filter
def convert_price(pln_price, curr):
    try:
        price = float(str(pln_price).replace(',', '.'))
        if abs(price - 199.95) < 0.01:
            return curr['p199']
        elif abs(price - 249.95) < 0.01:
            return curr['p249']
        else:
            divisor = curr.get('divisor', 1)
            raw = price / divisor
            return f"{math.floor(raw) + 0.95:.2f}"
    except (ValueError, TypeError, KeyError):
        return pln_price
    
@register.filter
def add_prices(price1, price2):
    try:
        return f"{float(str(price1)) + float(str(price2)):.2f}"
    except (ValueError, TypeError):
        return price1