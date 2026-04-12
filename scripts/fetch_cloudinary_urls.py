import os, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

import cloudinary
import cloudinary.api
import csv
from pathlib import Path
from decouple import config

cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUD_NAME'),
    api_key=config('CLOUDINARY_API_KEY'),
    api_secret=config('CLOUDINARY_API_SECRET'),
)

# Pobierz wszystkie zasoby z Cloudinary
print("Pobieranie listy zdjęć z Cloudinary...")
all_resources = []
next_cursor = None

while True:
    params = {'type': 'upload', 'max_results': 500}
    if next_cursor:
        params['next_cursor'] = next_cursor
    result = cloudinary.api.resources(**params)
    all_resources.extend(result['resources'])
    next_cursor = result.get('next_cursor')
    if not next_cursor:
        break

print(f"Znaleziono {len(all_resources)} zdjęć na Cloudinary")

# Zbuduj mapę: oryginalna_nazwa -> secure_url
url_map = {}
for r in all_resources:
    public_id = r['public_id']
    secure_url = r['secure_url']
    # Wyciągnij oryginalną nazwę (bez suffiksu i folderu)
    filename = Path(public_id).name
    # Usuń suffix (_rxtdg2 itp.)
    original = '_'.join(filename.split('_')[:-1]) if '_' in filename else filename
    url_map[original] = secure_url

# Zaktualizuj CSV
INPUT = Path('ai_import_clean.csv')
OUTPUT = Path('ai_import_cloudinary.csv')

rows = []
with open(INPUT, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        rows.append(row)

matched = 0
unmatched = 0
for row in rows:
    img_path = row.get('image', '')
    filename = Path(img_path).stem  # np. IMG-20260409-WA0000
    if filename in url_map:
        row['image'] = url_map[filename]
        matched += 1
    else:
        unmatched += 1
        print(f"Nie znaleziono: {filename}")

with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nDopasowano: {matched} | Nie znaleziono: {unmatched}")
print(f"Gotowe! -> {OUTPUT}")