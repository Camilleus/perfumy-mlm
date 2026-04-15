import os
import sys
import csv
import re
from django.utils.text import slugify

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from products.models import Product

GENDER_MAP = {'K': 'damskie', 'M': 'meskie', 'U': 'unisex'}

def clean_description(desc):
    desc = re.sub(r'\[.*?\]', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    if 'Pojemność:' not in desc:
        desc = f"Pojemność: 100 ml. {desc}"
    return desc

updated = 0
with open('ai_import_cloudinary.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        brand = row['brand']
        name = row['name']
        concentration = row['concentration']           # np. "edp", "edt", "parfum"
        gender_short = row['gender'].strip()
        gender_full = GENDER_MAP.get(gender_short, 'unisex')

        # Budowa sluga dokładnie tak, jak w Railway
        slug = slugify(f"{brand}-{name}-{concentration}-{gender_full}")

        try:
            product = Product.objects.get(slug=slug)
            product.description = clean_description(row['description'])
            product.save()
            updated += 1
            print(f"✓ {product.name} -> {slug}")
        except Product.DoesNotExist:
            print(f"✗ Nie znaleziono: {slug}")
        except Exception as e:
            print(f"✗ Błąd {slug}: {e}")

print(f"\nZaktualizowano {updated} produktów.")