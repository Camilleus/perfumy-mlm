#!/usr/bin/env python
"""
Skrypt do masowego importu zdjęć perfum.
Użycie:
1. Wrzuć wszystkie zdjęcia do folderu: media/products/raw/
2. Uruchom: python scripts/rename_images.py
3. Skrypt wygeneruje plik import_ready.csv gotowy do importu w adminie
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import csv
import shutil
from pathlib import Path

RAW_DIR = Path('media/products/raw')
OUT_DIR = Path('media/products')
CSV_OUT = Path('scripts/import_ready.csv')

def main():
    if not RAW_DIR.exists():
        RAW_DIR.mkdir(parents=True)
        print(f"Stworzono folder: {RAW_DIR}")
        print("Wrzuć zdjęcia do media/products/raw/ i uruchom ponownie.")
        return

    images = list(RAW_DIR.glob('*.jpg')) + list(RAW_DIR.glob('*.jpeg')) + list(RAW_DIR.glob('*.png')) + list(RAW_DIR.glob('*.webp'))

    if not images:
        print("Brak zdjęć w media/products/raw/")
        return

    print(f"Znaleziono {len(images)} zdjęć.")

    rows = []
    for img in sorted(images):
        dest = OUT_DIR / img.name
        shutil.copy2(img, dest)
        rows.append({
            'name': '',
            'brand': '',
            'slug': '',
            'price': '',
            'gender': '',
            'category': '',
            'concentration': 'edp',
            'scent_notes': '',
            'intensity': '',
            'occasion': '',
            'description': '',
            'stock_quantity': '10',
            'is_available': 'True',
            'image': f'products/{img.name}',
        })

    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Gotowe! Wygenerowano {CSV_OUT}")
    print(f"Wypełnij puste kolumny w pliku CSV, potem zaimportuj przez panel admina.")

if __name__ == '__main__':
    main()