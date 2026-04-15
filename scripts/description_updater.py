import csv, re
from django.utils.text import slugify
from products.models import Product

# Mapa skrótów na pełne nazwy używane w slugach
GENDER_MAP = {
    'K': 'damskie',
    'M': 'meskie',
    'U': 'unisex'
}

def clean_description(desc):
    # Usuń [reference:...] i podobne
    desc = re.sub(r'\[.*?\]', '', desc)
    # Normalizuj spacje
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Dodaj pojemność, jeśli brak
    if 'Pojemność:' not in desc and 'Pojemność' not in desc:
        desc = f"Pojemność: 100 ml. {desc}"
    return desc

updated = 0
with open('ai_import_cloudinary.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        brand = row['brand']
        name = row['name']
        gender_short = row['gender'].strip()
        gender_full = GENDER_MAP.get(gender_short, 'unisex')
        
        # Slug taki, jak w bazie (po skrypcie naprawczym)
        slug = slugify(f"{brand}-{name}-{gender_full}")
        
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