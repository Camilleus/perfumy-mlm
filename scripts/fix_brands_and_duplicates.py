import os
import sys
from collections import defaultdict
from django.db import transaction

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from products.models import Product
from orders.models import OrderItem, Sale

# ==================== MAPOWANIE MAREK ====================
BRAND_MAPPING = {
    # Paco Rabanne / Rabanne
    'Rabanne': 'Paco Rabanne',
    'Paco Rabanne': 'Paco Rabanne',
    
    # Giorgio Armani / Armani / Emporio Armani
    'Giorgio Armani': 'Armani',
    'Emporio Armani': 'Armani',
    'Armani': 'Armani',
    
    # Hugo Boss / BOSS
    'Hugo Boss': 'Hugo Boss',
    'BOSS': 'Hugo Boss',
    'BOSS Hugo Boss': 'Hugo Boss',
    
    # Jean Paul Gaultier
    'Jean Paul Gaultier': 'Jean Paul Gaultier',
    
    # Carolina Herrera
    'Carolina Herrera': 'Carolina Herrera',
    
    # Yves Saint Laurent
    'Yves Saint Laurent': 'Yves Saint Laurent',
    
    # Maison Francis Kurkdjian
    'Maison Francis Kurkdjian': 'Maison Francis Kurkdjian',
    'Maison Francis Kurkdjian Paris': 'Maison Francis Kurkdjian',
    
    # Tom Ford
    'Tom Ford': 'Tom Ford',
    
    # Louis Vuitton
    'Louis Vuitton': 'Louis Vuitton',
    
    # Xerjoff
    'Xerjoff': 'Xerjoff',
    
    # Parfums de Marly
    'Parfums de Marly': 'Parfums de Marly',
    
    # Kilian
    'Kilian': 'Kilian',
    
    # Kayali
    'KAYALI': 'Kayali',
    'Kayali': 'Kayali',
    
    # Gucci
    'Gucci': 'Gucci',
    
    # Chanel
    'Chanel': 'Chanel',
    
    # Dior
    'Dior': 'Dior',
    
    # Versace
    'Versace': 'Versace',
    
    # Givenchy
    'Givenchy': 'Givenchy',
    
    # Lancôme
    'Lancôme': 'Lancôme',
    'Lancome': 'Lancôme',
    
    # Bvlgari
    'Bvlgari': 'Bvlgari',
    
    # Valentino
    'Valentino': 'Valentino',
    
    # Moschino
    'Moschino': 'Moschino',
    
    # Creed
    'Creed': 'Creed',
    
    # Byredo
    'Byredo': 'Byredo',
    
    # Burberry
    'Burberry': 'Burberry',
    
    # Narciso Rodriguez
    'Narciso Rodriguez': 'Narciso Rodriguez',
    
    # Mugler
    'Mugler': 'Mugler',
    
    # Tiziana Terenzi
    'Tiziana Terenzi': 'Tiziana Terenzi',
    
    # Montblanc
    'Montblanc': 'Montblanc',
    
    # Essential Parfums
    'Essential Parfums': 'Essential Parfums',
    
    # Viktor & Rolf
    'Viktor & Rolf': 'Viktor & Rolf',
    
    # Ex Nihilo
    'Ex Nihilo': 'Ex Nihilo',
    
    # Guerlain
    'Guerlain': 'Guerlain',
    
    # Azzaro
    'Azzaro': 'Azzaro',
    
    # Gisada
    'Gisada': 'Gisada',
    
    # Philipp Plein
    'Philipp Plein': 'Philipp Plein',
    
    # Marc-Antoine Barrois
    'Marc-Antoine Barrois': 'Marc-Antoine Barrois',
    
    # Amouage
    'Amouage': 'Amouage',
    
    # Clive Christian
    'Clive Christian': 'Clive Christian',
    
    # Nasomatto
    'Nasomatto': 'Nasomatto',
    
    # Montale
    'Montale': 'Montale',
    
    # Mancera
    'Mancera': 'Mancera',
    
    # Penhaligon's
    'Penhaligon\'s': 'Penhaligon\'s',
    
    # Kenzo
    'Kenzo': 'Kenzo',
    
    # Michael Kors
    'Michael Kors': 'Michael Kors',
    
    # Jimmy Choo
    'Jimmy Choo': 'Jimmy Choo',
    
    # Zadig & Voltaire
    'Zadig & Voltaire': 'Zadig & Voltaire',
    
    # Victoria's Secret
    'Victoria\'s Secret': 'Victoria\'s Secret',
    
    # Calvin Klein
    'Calvin Klein': 'Calvin Klein',
    
    # Casamorati
    'Casamorati': 'Casamorati',
    
    # Dolce & Gabbana
    'Dolce & Gabbana': 'Dolce & Gabbana',
    
    # Chloé
    'Chloé': 'Chloé',
    'Chloe': 'Chloé',
    
    # Prada
    'Prada': 'Prada',
    
    # Morf
    'Morph': 'Morph',
    
    # Kajal
    'KAJAL': 'Kajal',
    'Kajal': 'Kajal',
    
    # Matiere Premiere
    'Matiere Premiere': 'Matiere Premiere',
    
    # Ducci Giardini di Toscana
    'Ducci Giardini di Toscana': 'Ducci Giardini di Toscana',
    
    # Escentric Molecules
    'Escentric Molecules': 'Escentric Molecules',
    
    # Pantheon Roma
    'Pantheon Roma': 'Pantheon Roma',
    
    # DSQUARED2
    'DSQUARED2': 'DSQUARED2',
}

def normalize_brand(brand):
    """Zwraca ujednoliconą nazwę marki."""
    if not brand:
        return brand
    # Usuń zbędne spacje i trim
    brand = brand.strip()
    # Mapowanie
    return BRAND_MAPPING.get(brand, brand)

def merge_products(dry_run=True):
    """
    Krok 1: Ujednolicenie marek.
    Krok 2: Usunięcie duplikatów (identyczne dane, różne zdjęcia/slug).
    """
    # ---------- KROK 1: Ujednolicenie marek ----------
    updated_brands = 0
    for product in Product.objects.all():
        old_brand = product.brand
        new_brand = normalize_brand(old_brand)
        if new_brand != old_brand:
            if not dry_run:
                product.brand = new_brand
                product.save()
            updated_brands += 1
            print(f"Zmiana marki: '{old_brand}' → '{new_brand}' dla {product.name}")
    
    if not dry_run:
        print(f"\n✅ Zaktualizowano {updated_brands} produktów (marki).")
    else:
        print(f"\n🔍 Znaleziono {updated_brands} produktów do zmiany marki (dry run).")
    
    # ---------- KROK 2: Wykrywanie i scalanie duplikatów ----------
    # Pola decydujące o duplikacji (pomijamy image, slug, stock_quantity, id)
    DUPLICATE_FIELDS = [
        'name', 'brand', 'gender', 'concentration', 'category',
        'intensity', 'occasion', 'scent_notes', 'description', 'price'
    ]
    
    def get_key(product):
        return tuple(getattr(product, field) for field in DUPLICATE_FIELDS)
    
    groups = defaultdict(list)
    for product in Product.objects.all():
        key = get_key(product)
        groups[key].append(product)
    
    total_groups = 0
    total_merged = 0
    
    for key, products in groups.items():
        if len(products) <= 1:
            continue
        
        total_groups += 1
        # Wybierz produkt główny: ten z większym stanem magazynowym, potem z wyższym ID
        main_product = max(products, key=lambda p: (p.stock_quantity, p.id))
        others = [p for p in products if p != main_product]
        
        print(f"\n📦 Grupa: {main_product.brand} {main_product.name} (ID głównego: {main_product.id})")
        print(f"   Duplikaty: {', '.join(str(p.id) for p in others)}")
        print(f"   Stan głównego: {main_product.stock_quantity}, suma duplikatów: {sum(p.stock_quantity for p in others)}")
        
        if dry_run:
            continue
        
        with transaction.atomic():
            # Zsumuj stany magazynowe
            total_stock = main_product.stock_quantity + sum(p.stock_quantity for p in others)
            main_product.stock_quantity = total_stock
            main_product.save()
            
            # Przenieś OrderItem i Sale
            for other in others:
                OrderItem.objects.filter(product=other).update(product=main_product)
                Sale.objects.filter(product=other).update(product=main_product)
                other.delete()
                total_merged += 1
            
            print(f"   ✅ Scalono. Nowy stan: {total_stock}")
    
    if dry_run:
        print(f"\n🔍 Znaleziono {total_groups} grup duplikatów. Uruchom z dry_run=False aby scalić.")
    else:
        print(f"\n✅ Scalono {total_merged} produktów.")

if __name__ == "__main__":
    # Najpierw w trybie podglądu
    merge_products(dry_run=True)
    
    # Jeśli wyniki OK, odkomentuj poniższą linię i uruchom ponownie
    merge_products(dry_run=False)