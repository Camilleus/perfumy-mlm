import os
import re
from pathlib import Path

TEMPLATES_DIR = Path('templates')
EXTENSIONS = ('.html',)

# Wykrywa bloki które należy pominąć w całości
SKIP_BLOCK_PATTERN = re.compile(
    r'(<script[\s\S]*?</script>|<style[\s\S]*?</style>|<!--[\s\S]*?-->)',
    re.IGNORECASE
)

# Tekst między tagami HTML (tylko między > a <)
TEXT_BETWEEN_TAGS = re.compile(r'(?<=>)([^<]+)(?=<)')

# Rzeczy które już są opakowane lub są zmiennymi Django
DJANGO_PATTERN = re.compile(r'\{[%{].*?[%}]\}', re.DOTALL)


def should_skip_text(text):
    stripped = text.strip()
    if not stripped:
        return True
    # Pomija jeśli tekst to same znaki specjalne / liczby
    if re.match(r'^[\d\s\.\,\:\;\-\_\|\(\)\/\\]+$', stripped):
        return True
    # Pomija jeśli zawiera już tagi Django
    if DJANGO_PATTERN.search(stripped):
        return True
    return False


def wrap_text(text):
    stripped = text.strip()
    # Zachowaj białe znaki wokół tekstu
    leading = text[:len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()):]
    # Cudzysłowy wewnątrz tekstu zastąp apostrofami
    safe = stripped.replace('"', "'")
    return f'{leading}{{% trans "{safe}" %}}{trailing}'


def process_line(line):
    # Pomijamy linie z tagami trans / blocktrans
    if '{% trans' in line or '{% blocktrans' in line:
        return line

    def replacer(match):
        original = match.group(1)
        if should_skip_text(original):
            return original
        return wrap_text(original)

    return TEXT_BETWEEN_TAGS.sub(replacer, line)


def split_preserving_blocks(content):
    """Dzieli zawartość na fragmenty: bloki do pominięcia i resztę."""
    parts = []
    last = 0
    for m in SKIP_BLOCK_PATTERN.finditer(content):
        parts.append(('process', content[last:m.start()]))
        parts.append(('skip', m.group(0)))
        last = m.end()
    parts.append(('process', content[last:]))
    return parts


def ensure_load_i18n(content):
    """Dodaje {% load i18n %} jeśli nie ma."""
    if '{% load i18n %}' in content or "{% load i18n%}" in content:
        return content
    # Wstaw po pierwszym tagu (np. po {% extends %} lub na początku)
    if content.startswith('{%'):
        first_newline = content.find('\n')
        if first_newline != -1:
            return content[:first_newline+1] + '{% load i18n %}\n' + content[first_newline+1:]
    return '{% load i18n %}\n' + content


def process_file(filepath):
    print(f"Przetwarzam: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Backup przed zmianami
    backup_path = filepath.with_suffix('.html.bak')
    if not backup_path.exists():
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

    parts = split_preserving_blocks(content)
    result_parts = []

    for kind, part in parts:
        if kind == 'skip':
            result_parts.append(part)
        else:
            processed_lines = [process_line(line) for line in part.splitlines(keepends=True)]
            result_parts.append(''.join(processed_lines))

    new_content = ensure_load_i18n(''.join(result_parts))

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)


def main():
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith(EXTENSIONS):
                process_file(Path(root) / file)


if __name__ == '__main__':
    main()