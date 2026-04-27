import os
import re
from pathlib import Path

TEMPLATES_DIR = Path('templates')
EXTENSIONS = ('.html',)

# Wyrażenie regularne: szukamy tekstu między tagami (ale nie w tagach i nie w atrybutach)
# Uwaga: to bardzo uproszczone – może zawieść przy zagnieżdżonych tagach, JS, itp.
TEXT_PATTERN = re.compile(r'(?<=>)([^<]+)(?=<)', re.DOTALL)

def should_skip(text):
    """Pomiń tekst, który jest pusty lub zawiera tylko białe znaki."""
    return not text.strip()

def wrap_line(line):
    """Opakowuje fragment tekstu w {% trans %}."""
    # Ignorujemy linie, które są już opakowane lub zawierają tagi trans
    if "{% trans" in line or "{% blocktrans" in line:
        return line
    # Szukamy tekstu między > a <
    def replacer(match):
        original = match.group(1)
        if should_skip(original):
            return original
        # Pomijamy, jeśli zawiera znaczniki HTML
        if '<' in original or '>' in original:
            return original
        # Pomijamy, jeśli to kod JavaScript
        if any(keyword in original for keyword in ['function', 'var ', 'const ', 'let ', 'return', '=>']):
            return original
        stripped = original.strip()
        if not stripped:
            return original
        # Zamieniamy na {% trans "tekst" %}
        return f'{{% trans "{stripped}" %}}'
    return TEXT_PATTERN.sub(replacer, line)

def process_file(filepath):
    print(f"Przetwarzam: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines = [wrap_line(line) for line in lines]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def main():
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith(EXTENSIONS):
                filepath = Path(root) / file
                process_file(filepath)

if __name__ == '__main__':
    main()