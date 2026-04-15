import csv
import re

def fix_slug(slug):
    # Usuń cyfry na końcu po myślniku (np. -1, -2)
    slug = re.sub(r'-\d+$', '', slug)
    # Zamień końcówki
    if slug.endswith('-k'):
        slug = slug[:-2] + '-damskie'
    elif slug.endswith('-m'):
        slug = slug[:-2] + '-meskie'
    elif slug.endswith('-u'):
        slug = slug[:-2] + '-unisex'
    return slug

input_file = 'ai_import_cloudinary.csv'
output_file = 'ai_import_cloudinary_fixed.csv'

with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8', newline='') as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in reader:
        row['slug'] = fix_slug(row['slug'])
        writer.writerow(row)

print(f"Gotowe! Poprawiony plik: {output_file}")