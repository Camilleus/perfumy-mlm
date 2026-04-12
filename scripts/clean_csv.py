#!/usr/bin/env python
"""
Skrypt czyszczący CSV po analizie AI.
Użycie: python scripts/clean_csv.py
"""

import csv
import re
from pathlib import Path

INPUT = Path('scripts/ai_import.csv')
OUTPUT = Path('scripts/ai_import_clean.csv')

GENDER_MAP = {
    'f': 'K', 'w': 'K', 'k': 'K', 'women': 'K', 'woman': 'K', 'female': 'K', 'damskie': 'K',
    'm': 'M', 'men': 'M', 'man': 'M', 'male': 'M', 'meskie': 'M', 'męskie': 'M',
    'u': 'U', 'unisex': 'U',
}

CATEGORY_MAP = {
    'floral-fruity': 'floral', 'floral fruity': 'floral', 'kwiatowy': 'floral',
    'kwiatowe': 'floral', 'kwiatowo-owocowe': 'floral', 'flower': 'floral',
    'drzewne': 'woody', 'drzewny': 'woody', 'wood': 'woody', 'drewno': 'woody',
    'świeże': 'fresh', 'swieże': 'fresh', 'swiezе': 'fresh', 'citrusy': 'fresh',
    'orientalne': 'oriental', 'orientalny': 'oriental', 'orient': 'oriental',
    'cytrusowe': 'citrus', 'cytrusowy': 'citrus', 'citrus fruits': 'citrus',
}

CONCENTRATION_MAP = {
    'eau de toilette': 'edt', 'eau de parfum': 'edp', 'eau de cologne': 'edt',
    'toaletowa': 'edt', 'woda toaletowa': 'edt', 'woda perfumowana': 'edp',
    'eau de parfum (edp)': 'edp', 'eau de toilette (edt)': 'edt',
    'perfume': 'parfum', 'perfumy': 'parfum', 'extrait': 'parfum',
    'ekstrakt': 'parfum', 'extrait de parfum': 'parfum',
    'cologne': 'edt', 'body mist': 'edt',
}

INTENSITY_MAP = {
    'umiarkowana': 'light', 'moderate': 'light', 'delikatna': 'light',
    'light to moderate': 'light', 'moderate to strong': 'strong',
    'intensywna': 'strong', 'silna': 'strong', 'mocna': 'strong',
}

OCCASION_MAP = {
    'casual': 'daily', 'dzień': 'daily', 'dzien': 'daily', 'codzienne': 'daily',
    'everyday': 'daily', 'day': 'daily', 'wieczór': 'special', 'wieczor': 'special',
    'evening': 'special', 'night': 'special', 'versatile': 'daily',
}

def clean_gender(val):
    return GENDER_MAP.get(val.lower().strip(), 'U')

def clean_category(val):
    return CATEGORY_MAP.get(val.lower().strip(), val.lower().strip() if val.lower().strip() in ['floral', 'woody', 'fresh', 'oriental', 'citrus'] else 'floral')

def clean_concentration(val):
    return CONCENTRATION_MAP.get(val.lower().strip(), val.lower().strip() if val.lower().strip() in ['edt', 'edp', 'parfum'] else 'edp')

def clean_intensity(val):
    return INTENSITY_MAP.get(val.lower().strip(), val.lower().strip() if val.lower().strip() in ['light', 'strong'] else 'light')

def clean_occasion(val):
    return OCCASION_MAP.get(val.lower().strip(), val.lower().strip() if val.lower().strip() in ['daily', 'special'] else 'daily')

def clean_scent_notes(val):
    # Usuń tagi cite
    val = re.sub(r'<cite[^>]*>|</cite>', '', val)
    # Zamień polskie nazwy na angielskie
    val = val.replace('Nuty głowy:', 'Top:').replace('Nuty głowy :', 'Top:')
    val = val.replace('Nuty serca:', 'Heart:').replace('Nuty serca :', 'Heart:')
    val = val.replace('Nuty bazy:', 'Base:').replace('Nuty bazy :', 'Base:')
    val = val.replace('Głowa:', 'Top:').replace('Serce:', 'Heart:').replace('Baza:', 'Base:')
    return val.strip()

def clean_description(val):
    # Usuń tagi cite
    val = re.sub(r'<cite[^>]*>|</cite>', '', val)
    return val.strip()

def clean_slug(slug, brand, name, gender):
    import os, sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    import django
    try:
        django.setup()
    except RuntimeError:
        pass
    from django.utils.text import slugify
    # Usuń markę z nazwy jeśli się powtarza
    brand_lower = brand.lower().strip()
    name_clean = name.strip()
    if name_clean.lower().startswith(brand_lower):
        name_clean = name_clean[len(brand):].strip()
    gender_slug = gender.lower()
    return slugify(f"{brand}-{name_clean}-{gender_slug}")

def main():
    rows = []
    with open(INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gender = clean_gender(row['gender'])
            row['gender'] = gender
            row['category'] = clean_category(row['category'])
            row['concentration'] = clean_concentration(row['concentration'])
            row['intensity'] = clean_intensity(row['intensity'])
            row['occasion'] = clean_occasion(row['occasion'])
            row['scent_notes'] = clean_scent_notes(row['scent_notes'])
            row['description'] = clean_description(row['description'])
            row['slug'] = clean_slug(row['slug'], row['brand'], row['name'], gender)
            rows.append(row)

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Gotowe! Wyczyszczono {len(rows)} wierszy -> {OUTPUT}")

    # Podsumowanie problemów
    problems = [r for r in rows if r['gender'] == 'U' and 'NIEZNANE' not in r['name']]
    if problems:
        print(f"Uwaga: {len(problems)} produktów z płcią U – sprawdź ręcznie")

if __name__ == '__main__':
    main()