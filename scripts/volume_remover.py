import os
import sys
import re

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from products.models import Product

def clean_description(desc):
    # Usuń "Pojemność: 100 ml." (z różnymi wariantami)
    pattern = r'Pojemność:\s*100\s*ml\.?\s*'
    desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
    # Usuń podwójne spacje i przecinki powstałe po usunięciu
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Jeśli na początku został przecinek lub kropka, usuń
    desc = re.sub(r'^[,.]\s*', '', desc)
    return desc

updated = 0
for product in Product.objects.all():
    if product.description:
        new_desc = clean_description(product.description)
        if new_desc != product.description:
            product.description = new_desc
            product.save()
            updated += 1
            print(f"✓ {product.name}")
print(f"\nZaktualizowano {updated} produktów.")