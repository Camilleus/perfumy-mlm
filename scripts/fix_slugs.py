import os, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from products.models import Product
from django.utils.text import slugify

fixed = 0
for p in Product.objects.filter(slug=''):
    p.slug = slugify(f"{p.brand}-{p.name}-{p.gender.lower()}")
    p.save()
    fixed += 1

print(f"Naprawiono {fixed} produktów")