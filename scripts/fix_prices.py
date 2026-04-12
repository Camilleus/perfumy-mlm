import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from decimal import Decimal
from products.models import Product

PREMIUM_BRANDS = ['xerjoff', 'amouage', 'phillip plein', 'philipp plein']

updated = 0

for product in Product.objects.all():
    brand_lower = product.brand.lower()
    is_premium = any(b in brand_lower for b in PREMIUM_BRANDS)

    new_price = Decimal('249.95') if is_premium else Decimal('199.95')

    if product.price != new_price:
        product.price = new_price
        product.save()
        updated += 1

print(f"Zaktualizowano {updated} produktów.")
print("Gotowe! ✅")