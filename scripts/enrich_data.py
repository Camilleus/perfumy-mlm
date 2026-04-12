#!/usr/bin/env python
"""
Skrypt 2: Sonnet wyszukuje dane o perfumach bez analizy zdjęć.
Użycie: python scripts/enrich_data.py
"""

import os
import sys
import csv
import time
import re
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from decouple import config
import anthropic

client = anthropic.Anthropic(api_key=config('ANTHROPIC_API_KEY'))

INPUT = Path('scripts/identified.csv')
CSV_OUT = Path('scripts/ai_import.csv')
PROGRESS_FILE = Path('scripts/enrich_progress.txt')

PROMPT_TEMPLATE = """Podaj dane o perfumach "{name}" marki "{brand}" w formacie JSON.
Odpowiedz TYLKO JSON, bez tekstu przed ani po.

{{
  "gender": "K lub M lub U",
  "gender_slug": "k lub m lub u",
  "category": "TYLKO jedno z: floral, woody, fresh, oriental, citrus",
  "concentration": "TYLKO jedno z: edt, edp, parfum",
  "intensity": "TYLKO jedno z: light, strong",
  "occasion": "TYLKO jedno z: daily, special",
  "price": 200
}}

ZASADY:
- Odpowiadaj tylko na podstawie pewnej wiedzy
- price: 200 (250 dla Xerjoff, Phillip Plein, Amouage)
- Bez opisów, bez nut zapachowych
- Tylko te 7 pól
"""

def enrich_product(name, brand):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(name=name, brand=brand)
            }
        ]
    )

    full_text = ""
    for block in message.content:
        if hasattr(block, 'text'):
            full_text += block.text

    match = re.search(r'\{.*\}', full_text, re.DOTALL)
    if not match:
        raise ValueError(f"Brak JSON: {full_text[:200]}")

    result = json.loads(match.group())
    for key in ['scent_notes', 'description']:
        if key in result:
            result[key] = re.sub(r'<cite[^>]*>|</cite>', '', str(result[key])).strip()
    return result

def load_progress():
    if PROGRESS_FILE.exists():
        return set(PROGRESS_FILE.read_text().strip().split('\n'))
    return set()

def save_progress(image):
    with open(PROGRESS_FILE, 'a') as f:
        f.write(image + '\n')

def main():
    rows = []
    with open(INPUT, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    done = load_progress()
    remaining = [r for r in rows if r['image'] not in done]

    print(f"Łącznie: {len(rows)} | Zrobione: {len(done)} | Pozostało: {len(remaining)}")

    from django.utils.text import slugify

    fieldnames = ['name', 'brand', 'slug', 'price', 'gender', 'category', 'concentration',
                  'scent_notes', 'intensity', 'occasion', 'description', 'stock_quantity',
                  'is_available', 'image']

    file_exists = CSV_OUT.exists()
    with open(CSV_OUT, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for i, row in enumerate(remaining, 1):
            name = row['name']
            brand = row['brand']
            image = row['image']

            if name == 'NIEZNANE' or brand == 'NIEZNANE':
                print(f"[{i}/{len(remaining)}] Pomijam NIEZNANE: {image}")
                save_progress(image)
                continue

            print(f"[{i}/{len(remaining)}] {brand} - {name}...", end=' ', flush=True)
            try:
                data = enrich_product(name, brand)
                gender = data.get('gender', 'U')
                gender_slug = data.get('gender_slug', gender.lower())
                slug = slugify(f"{brand}-{name}-{gender_slug}")

                writer.writerow({
                    'name': name,
                    'brand': brand,
                    'slug': slug,
                    'price': data.get('price', 200),
                    'gender': data.get('gender', 'U'),
                    'category': data.get('category', 'floral'),
                    'concentration': data.get('concentration', 'edp'),
                    'scent_notes': '',
                    'intensity': data.get('intensity', 'light'),
                    'occasion': data.get('occasion', 'daily'),
                    'description': '',
                    'stock_quantity': 10,
                    'is_available': True,
                    'image': image,
                })
                f.flush()
                save_progress(image)
                print(f"✓")
                time.sleep(3)

            except Exception as e:
                err = str(e)
                if '429' in err or 'rate_limit' in err.lower():
                    print(f"⏳ rate limit, czekam 60s...")
                    time.sleep(60)
                elif '529' in err or 'overloaded' in err.lower():
                    print(f"⏳ przeciążony, czekam 30s...")
                    time.sleep(30)
                else:
                    print(f"✗ błąd: {e}")
                    time.sleep(2)

    print(f"\nGotowe! Wynik: {CSV_OUT}")

if __name__ == '__main__':
    main()