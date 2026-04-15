import csv
import re

input_file = 'ai_import_cloudinary.csv'
output_file = 'ai_import_cloudinary.csv'

with open(input_file, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

fieldnames = list(rows[0].keys())

cleaned = 0

for row in rows:
    desc = row.get('description', '')

    # Usuń [reference:X]
    desc = re.sub(r'\[reference:\d+\]', '', desc)

    # Usuń podwójne spacje i spacje przed kropką
    desc = re.sub(r' +', ' ', desc)
    desc = re.sub(r' \.', '.', desc)
    desc = desc.strip()

    # Dodaj pojemność na początku jeśli jej nie ma
    if desc and '100ml' not in desc and '100 ml' not in desc:
        desc = 'Pojemność: 100ml. ' + desc

    if row['description'] != desc:
        cleaned += 1

    row['description'] = desc

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wyczyszczono {cleaned} opisów. ✅")