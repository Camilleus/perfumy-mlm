import os, sys, csv
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from products.models import Product
from pathlib import Path

INPUT = Path('ai_import_cloudinary.csv')

rows = []
with open(INPUT, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

updated = 0
not_found = 0

for row in rows:
    slug = row.get('slug', '')
    image_url = row.get('image', '')
    if not slug or not image_url.startswith('http'):
        continue
    try:
        p = Product.objects.get(slug=slug)
        p.image = image_url
        p.save()
        updated += 1
    except Product.DoesNotExist:
        not_found += 1

print(f"Zaktualizowano: {updated} | Nie znaleziono: {not_found}")