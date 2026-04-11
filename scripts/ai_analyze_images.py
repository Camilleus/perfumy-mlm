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

PROMPT = """Analizujesz zdjęcie perfum. Odpowiedz TYLKO w formacie JSON, bez żadnego tekstu przed ani po. Bez tagów <cite>, bez przypisów, bez cudzysłowów zagnieżdżonych.

PRZYKŁAD POPRAWNEJ ODPOWIEDZI:
{
  "name": "Sauvage Elixir",
  "brand": "Dior",
  "gender": "M",
  "gender_slug": "m",
  "category": "TYLKO jedno z tych słów: floral, woody, fresh, oriental, citrus",
  "concentration": "parfum",
  "intensity": "TYLKO jedno z tych słów: light, strong",
  "occasion": "TYLKO jedno z tych słów: daily, special",
  "scent_notes": "Top: grejpfrut, kanelowiec; Heart: lawenda, geranium; Base: cedr, piżmo, ambra",
  "description": "Sauvage Elixir to ultraskoncentrowana wersja kultowego Diora, stworzona dla mężczyzn poszukujących intensywnego i wyrazistego zapachu. Otwiera się świeżą nutą grejpfruta i aromatycznym cynamonem, przechodząc w serce z lawendą i geranium. Głęboka baza cedru i ambry nadaje kompozycji trwałość i zmysłowy charakter. Idealny na wieczory i wyjątkowe okazje.",
  "price": 200
}

ZASADY:
- Wszystkie opisy i nuty po polsku
- scent_notes ZAWSZE w formacie: Top: ...; Heart: ...; Base: ...
- Bez tagów HTML, bez przypisów, bez <cite>
- Płeć na podstawie konkretnej wersji widocznej na zdjęciu
- Cena zawsze 200 (chyba że marka to Xerjoff, Phillip Plein lub Amouage - wtedy 250)
- Opis: 3-4 zdania, tylko po polsku, bez zapożyczeń z innych języków
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
    import re as re2
    result = json.loads(match.group())
    for key in ['scent_notes', 'description', 'name', 'brand']:
        if key in result:
            result[key] = re2.sub(r'<cite[^>]*>|</cite>', '', str(result[key])).strip()
    return result

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
                gender_slug = data.get('gender_slug', 'u')
                slug = slugify(f"{data.get('brand', '')}-{data.get('name', '')}-{gender_slug}")

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
                time.sleep(2)

            except Exception as e:
                err = str(e)
                if '529' in err or 'overloaded' in err.lower():
                    print(f"⏳ przeciążony, czekam 30s...")
                    time.sleep(30)
                else:
                    print(f"✗ błąd: {e}")
                    time.sleep(2)

    print(f"\nGotowe! Wynik: {CSV_OUT}")

if __name__ == '__main__':
    main()