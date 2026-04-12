#!/usr/bin/env python
"""
Skrypt czyszczący ai_import.csv
Użycie: python clean_csv.py ai_import.csv
"""

import csv
import re
import sys
from pathlib import Path

INPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('ai_import.csv')
OUTPUT = Path('ai_import_clean.csv')

GENDER_MAP = {
    'f': 'K', 'w': 'K', 'k': 'K', 'women': 'K', 'woman': 'K',
    'female': 'K', 'damskie': 'K', 'kobieta': 'K',
    'm': 'M', 'men': 'M', 'man': 'M', 'male': 'M',
    'meskie': 'M', 'męskie': 'M', 'mężczyzna': 'M',
    'u': 'U', 'unisex': 'U',
}

CATEGORY_MAP = {
    'floral-fruity': 'floral', 'floral fruity': 'floral',
    'kwiatowy': 'floral', 'kwiatowe': 'floral', 'kwiatowo-owocowe': 'floral',
    'drzewne': 'woody', 'drzewny': 'woody', 'wood': 'woody',
    'świeże': 'fresh', 'fresh citrus': 'fresh', 'citrusy': 'fresh',
    'orientalne': 'oriental', 'orientalny': 'oriental', 'amber': 'oriental',
    'cytrusowe': 'citrus', 'cytrusowy': 'citrus',
}

CONCENTRATION_MAP = {
    'eau de toilette': 'edt', 'eau de parfum': 'edp', 'eau de cologne': 'edt',
    'toaletowa': 'edt', 'woda toaletowa': 'edt', 'woda perfumowana': 'edp',
    'extrait de parfum': 'parfum', 'extrait': 'parfum',
    'perfume': 'parfum', 'perfumy': 'parfum',
}

INTENSITY_MAP = {
    'umiarkowana': 'light', 'moderate': 'light', 'delikatna': 'light',
    'light to moderate': 'light', 'moderate to strong': 'strong',
    'intensywna': 'strong', 'silna': 'strong', 'mocna': 'strong',
}

OCCASION_MAP = {
    'casual': 'daily', 'dzień': 'daily', 'dzien': 'daily',
    'codzienne': 'daily', 'everyday': 'daily', 'day': 'daily',
    'wieczór': 'special', 'evening': 'special', 'night': 'special',
    'versatile': 'daily',
}

VALID_GENDERS = {'K', 'M', 'U'}
VALID_CATEGORIES = {'floral', 'woody', 'fresh', 'oriental', 'citrus'}
VALID_CONCENTRATIONS = {'edt', 'edp', 'parfum'}
VALID_INTENSITIES = {'light', 'strong'}
VALID_OCCASIONS = {'daily', 'special'}


def normalize(val, mapping, valid_set, default):
    v = val.lower().strip()
    if v in valid_set:
        return v.upper() if valid_set == VALID_GENDERS else v
    return mapping.get(v, default)


def clean_gender(val):
    v = val.lower().strip()
    if v in {'k', 'f', 'w', 'women', 'woman', 'female', 'damskie'}:
        return 'K'
    if v in {'m', 'men', 'man', 'male', 'meskie', 'männlich'}:
        return 'M'
    return 'U'


def clean_slug(brand, name, gender):
    import unicodedata

    def slugify(text):
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text.strip('-')

    gender_slug = gender.lower()
    # Usuń markę z nazwy jeśli się powtarza
    brand_lower = brand.lower().strip()
    name_clean = name.strip()
    if name_clean.lower().startswith(brand_lower + ' '):
        name_clean = name_clean[len(brand):].strip()

    return slugify(f"{brand}-{name_clean}-{gender_slug}")


def clean_scent_notes(val):
    if not val:
        return val
    val = re.sub(r'<cite[^>]*>|</cite>', '', val)
    val = val.replace('Nuty głowy:', 'Top:').replace('Nuty głowy :', 'Top:')
    val = val.replace('Nuty serca:', 'Heart:').replace('Nuty serca :', 'Heart:')
    val = val.replace('Nuty bazy:', 'Base:').replace('Nuty bazy :', 'Base:')
    val = val.replace('Głowa:', 'Top:').replace('Serce:', 'Heart:').replace('Baza:', 'Base:')
    return val.strip()


def clean_description(val):
    if not val:
        return val
    val = re.sub(r'<cite[^>]*>|</cite>', '', val)
    return val.strip()


def main():
    rows = []
    with open(INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    print(f"Wczytano {len(rows)} wierszy")
    fixed = 0

    seen_slugs = {}
    output_rows = []

    for row in rows:
        brand = row.get('brand', '').strip()
        name = row.get('name', '').strip()
        gender_raw = row.get('gender', 'U')

        gender = clean_gender(gender_raw)
        if gender != gender_raw:
            fixed += 1

        category_raw = row.get('category', 'floral')
        category = normalize(category_raw, CATEGORY_MAP, VALID_CATEGORIES, 'floral')
        if category != category_raw:
            fixed += 1

        concentration_raw = row.get('concentration', 'edp')
        concentration = normalize(concentration_raw, CONCENTRATION_MAP, VALID_CONCENTRATIONS, 'edp')
        if concentration != concentration_raw:
            fixed += 1

        intensity_raw = row.get('intensity', 'light')
        intensity = normalize(intensity_raw, INTENSITY_MAP, VALID_INTENSITIES, 'light')
        if intensity != intensity_raw:
            fixed += 1

        occasion_raw = row.get('occasion', 'daily')
        occasion = normalize(occasion_raw, OCCASION_MAP, VALID_OCCASIONS, 'daily')
        if occasion != occasion_raw:
            fixed += 1

        # Napraw slug
        slug = clean_slug(brand, name, gender)

        # Obsłuż duplikaty slugów
        if slug in seen_slugs:
            seen_slugs[slug] += 1
            slug = f"{slug}-{seen_slugs[slug]}"
        else:
            seen_slugs[slug] = 0

        row['gender'] = gender
        row['category'] = category
        row['concentration'] = concentration
        row['intensity'] = intensity
        row['occasion'] = occasion
        PREMIUM_BRANDS = ['xerjoff', 'amouage', 'phillip plein', 'philipp plein']
        PREMIUM_NAMES = ['skull', 'czaszka', '$kull']

        brand_lower = row['brand'].lower()
        name_lower = row['name'].lower()

        if any(b in brand_lower for b in PREMIUM_BRANDS):
            row['price'] = '250'
        elif 'plein' in brand_lower and any(n in name_lower for n in PREMIUM_NAMES):
            row['price'] = '250'
        row['slug'] = slug
        row['scent_notes'] = clean_scent_notes(row.get('scent_notes', ''))
        row['description'] = clean_description(row.get('description', ''))

        output_rows.append(row)

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Naprawiono {fixed} wartości")
    print(f"Zapisano {len(output_rows)} wierszy -> {OUTPUT}")

    # Podsumowanie
    from collections import Counter
    print("\nPo czyszczeniu:")
    print("GENDER:", dict(Counter(r['gender'] for r in output_rows)))
    print("CATEGORY:", dict(Counter(r['category'] for r in output_rows)))
    print("CONCENTRATION:", dict(Counter(r['concentration'] for r in output_rows)))
    print("INTENSITY:", dict(Counter(r['intensity'] for r in output_rows)))
    print("OCCASION:", dict(Counter(r['occasion'] for r in output_rows)))


if __name__ == '__main__':
    main()