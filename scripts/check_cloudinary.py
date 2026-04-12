import os, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

import cloudinary
import cloudinary.api
from decouple import config

cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUD_NAME'),
    api_key=config('CLOUDINARY_API_KEY'),
    api_secret=config('CLOUDINARY_API_SECRET'),
)

result = cloudinary.api.resources(type='upload', max_results=3)
for r in result['resources']:
    print(r['public_id'])
    print(r['secure_url'])
    print()