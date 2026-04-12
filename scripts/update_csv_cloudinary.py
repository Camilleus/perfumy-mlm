#!/usr/bin/env python
"""
Aktualizuje CSV zastępując lokalne ścieżki URL-ami Cloudinary.
Użycie: python scripts/update_csv_cloudinary.py
"""

import csv
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

import cloudinary
import cloudinary.api
from decouple import config

cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUD_NAME'),
    api_key=config('CLOUDINARY_API_KEY'),
    api_secret=config('CLOUDINARY_API_SECRET'),
)

INPUT = Path('ai_import_clean.csv')
OUTPUT = Path('ai_import_cloudinary.csv')
CLOUDINARY_FOLDER = 'home/perfumy'

def get_cloudinary_url(filename):
    public_id = f"{CLOUDINARY_FOLDER}/{Path(filename).stem}"
    url = cloudinary.utils.cloudinary_url(public_id + '.jpg')[0]
    return url

def main():
    rows = []
    with open(INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    print(f"Wczytano {len(rows)} wierszy")

    for i, row in enumerate(rows, 1):
        old_image = row.get('image', '')
        filename = Path(old_image).name
        new_url = get_cloudinary_url(filename)
        row['image'] = new_url
        if i % 50 == 0:
            print(f"Przetworzono {i}/{len(rows)}")

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Gotowe! -> {OUTPUT}")

if __name__ == '__main__':
    main()