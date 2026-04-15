import csv
import re
from products.models import Product

def clean_description(desc):
    # Usuń wszystko w nawiasach kwadratowych (np. [reference:17])
    desc = re.sub(r'\[.*?\]', '', desc)
    # Znormalizuj spacje
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Dodaj pojemność, jeśli jej nie ma
    if 'Pojemność:' not in desc and 'Pojemność' not in desc:
        desc = f"Pojemność: 100 ml. {desc}"
    return desc

updated = 0
with open('ai_import_cloudinary.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        slug = row['slug']
        new_desc = clean_description(row['description'])
        try:
            product = Product.objects.get(slug=slug)
            product.description = new_desc
            product.save()
            updated += 1
            print(f"✓ {product.name}")
        except Product.DoesNotExist:
            print(f"✗ Nie znaleziono: {slug}")
        except Exception as e:
            print(f"✗ Błąd {slug}: {e}")

print(f"\nZaktualizowano {updated} produktów.")