#!/usr/bin/env python
"""
Skrypt do automatycznej analizy zdjęć perfum przez Claude AI.
Użycie: python scripts/ai_analyze_images.py
"""

import os
import sys
import django
import base64
import csv
import time
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from decouple import config
import anthropic

client = anthropic.Anthropic(api_key=config('ANTHROPIC_API_KEY'))

RAW_DIR = Path('media/products/raw')
CSV_OUT = Path('scripts/ai_import.csv')
PROGRESS_FILE = Path('scripts/ai_progress.txt')

PROMPT = """Analizujesz zdjęcie perfum. Odpowiedz TYLKO w formacie JSON, bez żadnego tekstu przed ani po.

{
  "name": "pełna nazwa perfum bez marki",
  "brand": "marka",
  "gender": "K lub M lub U (K=damskie, M=męskie, U=unisex)",
  "category": "jedno z: floral, woody, fresh, oriental, citrus",
  "concentration": "jedno z: edt, edp, parfum",
  "intensity": "jedno z: light, strong",
  "occasion": "jedno z: daily, special",
  "scent_notes": "nuty zapachowe po polsku: Top: ...; Heart: ...; Base: ...",
  "description": "szczegółowy opis po polsku, 3-4 zdania: historia, charakter, do kogo skierowane, na jaką okazję",
  "price": 200
}

Użyj swojej wiedzy o perfumach – nie tylko tego co widzisz na zdjęciu.
Jeśli rozpoznajesz produkt, podaj pełne i dokładne informacje.
Jeśli nie rozpoznajesz, wpisz "NIEZNANE" dla name i brand.
Cena zawsze 200.
"""

def analyze_image(image_path):
    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    ext = image_path.suffix.lower()
    media_type_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
    media_type = media_type_map.get(ext, 'image/jpeg')

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": PROMPT}
                ]
            }
        ]
    )

    import json
    import re

    full_text = ""
    for block in message.content:
        if hasattr(block, 'text'):
            full_text += block.text

    match = re.search(r'\{.*\}', full_text, re.DOTALL)
    if not match:
        raise ValueError(f"Brak JSON w odpowiedzi: {full_text[:200]}")
    return json.loads(match.group())

def load_progress():
    if PROGRESS_FILE.exists():
        return set(PROGRESS_FILE.read_text().strip().split('\n'))
    return set()

def save_progress(filename):
    with open(PROGRESS_FILE, 'a') as f:
        f.write(filename + '\n')

def main():
    images = sorted(
        list(RAW_DIR.glob('*.jpg')) +
        list(RAW_DIR.glob('*.jpeg')) +
        list(RAW_DIR.glob('*.png')) +
        list(RAW_DIR.glob('*.webp'))
    )

    if not images:
        print("Brak zdjęć w media/products/raw/")
        return

    done = load_progress()
    remaining = [i for i in images if i.name not in done]

    print(f"Łącznie: {len(images)} | Zrobione: {len(done)} | Pozostało: {len(remaining)}")

    fieldnames = ['name', 'brand', 'slug', 'price', 'gender', 'category', 'concentration', 'scent_notes', 'intensity', 'occasion', 'description', 'stock_quantity', 'is_available', 'image']

    file_exists = CSV_OUT.exists()
    with open(CSV_OUT, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for i, img in enumerate(remaining, 1):
            print(f"[{i}/{len(remaining)}] {img.name}...", end=' ', flush=True)
            try:
                data = analyze_image(img)
                from django.utils.text import slugify
                slug = slugify(f"{data.get('brand', '')}-{data.get('name', '')}")

                writer.writerow({
                    'name': data.get('name', 'NIEZNANE'),
                    'brand': data.get('brand', 'NIEZNANE'),
                    'slug': slug,
                    'price': data.get('price') or 200,
                    'gender': data.get('gender', 'U'),
                    'category': data.get('category', 'floral'),
                    'concentration': data.get('concentration', 'edp'),
                    'scent_notes': data.get('scent_notes', ''),
                    'intensity': data.get('intensity', 'light'),
                    'occasion': data.get('occasion', 'daily'),
                    'description': data.get('description', ''),
                    'stock_quantity': 10,
                    'is_available': True,
                    'image': f'products/{img.name}',
                })
                f.flush()
                save_progress(img.name)
                print(f"✓ {data.get('brand')} - {data.get('name')}")
                time.sleep(0.5)

            except Exception as e:
                print(f"✗ błąd: {e}")
                time.sleep(1)

    print(f"\nGotowe! Wynik: {CSV_OUT}")

if __name__ == '__main__':
    main()