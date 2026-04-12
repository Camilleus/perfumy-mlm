#!/usr/bin/env python
"""
Skrypt 1: Haiku identyfikuje nazwę i markę ze zdjęcia.
Użycie: python scripts/identify_images.py
"""

import os
import sys
import base64
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

RAW_DIR = Path('media/products/raw')
CSV_OUT = Path('scripts/identified.csv')
PROGRESS_FILE = Path('scripts/identify_progress.txt')

PROMPT = """Patrz na zdjęcie perfum. Odpowiedz TYLKO w formacie JSON:

{"name": "nazwa perfum bez marki, WŁĄCZNIE z typem jeśli widoczny (np. Sauvage Eau de Parfum, Sauvage Parfum)", "brand": "marka"}

Tylko te dwa pola. Jeśli nie możesz odczytać, wpisz "NIEZNANE".
Bez żadnego tekstu poza JSON."""

def identify_image(image_path):
    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    ext = image_path.suffix.lower()
    media_type_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
    media_type = media_type_map.get(ext, 'image/jpeg')

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
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

    text = message.content[0].text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"Brak JSON: {text[:100]}")
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

    done = load_progress()
    # Wczytaj już zidentyfikowane z identified.csv
    if CSV_OUT.exists():
        with open(CSV_OUT, 'r', encoding='utf-8') as existing:
            for r in csv.DictReader(existing):
                img_name = Path(r['image']).name
                done.add(img_name)
        print(f"Już w identified.csv: {len(done)}")

    # Wczytaj już przetworzone z ai_import.csv
    ai_import = Path('scripts/ai_import.csv')
    if ai_import.exists():
        with open(ai_import, 'r', encoding='utf-8') as existing:
            for r in csv.DictReader(existing):
                img_name = Path(r['image']).name
                done.add(img_name)
        print(f"Już w ai_import.csv: {len(done)}")
    remaining = [i for i in images if i.name not in done]

    print(f"Łącznie: {len(images)} | Zrobione: {len(done)} | Pozostało: {len(remaining)}")

    file_exists = CSV_OUT.exists()
    with open(CSV_OUT, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['image', 'name', 'brand'])
        if not file_exists:
            writer.writeheader()

        for i, img in enumerate(remaining, 1):
            print(f"[{i}/{len(remaining)}] {img.name}...", end=' ', flush=True)
            try:
                data = identify_image(img)
                writer.writerow({
                    'image': f'products/{img.name}',
                    'name': data.get('name', 'NIEZNANE'),
                    'brand': data.get('brand', 'NIEZNANE'),
                })
                f.flush()
                save_progress(img.name)
                print(f"✓ {data.get('brand')} - {data.get('name')}")
                time.sleep(1)

            except Exception as e:
                err = str(e)
                if '429' in err or 'rate_limit' in err.lower():
                    print(f"⏳ rate limit, czekam 30s...")
                    time.sleep(30)
                elif '529' in err or 'overloaded' in err.lower():
                    print(f"⏳ przeciążony, czekam 20s...")
                    time.sleep(20)
                else:
                    print(f"✗ błąd: {e}")
                    time.sleep(2)

    print(f"\nGotowe! Wynik: {CSV_OUT}")

if __name__ == '__main__':
    main()