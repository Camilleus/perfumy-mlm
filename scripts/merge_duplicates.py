import os
import sys
from collections import defaultdict
from django.db import transaction

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from products.models import Product
from orders.models import OrderItem
from sellers.models import Sale

# Pola decydujące o duplikacji (pomijamy image, slug, stock_quantity, is_available, id)
DUPLICATE_FIELDS = [
    'name', 'brand', 'gender', 'concentration', 'category',
    'intensity', 'occasion', 'scent_notes', 'description', 'price'
]

def get_key(product):
    """Zwraca krotkę wartości pól – identyfikator grupy duplikatów"""
    return tuple(getattr(product, field) for field in DUPLICATE_FIELDS)

def merge_products(dry_run=True):
    """
    dry_run=True – tylko wyświetla, co zostanie scalone (bez zmian w bazie)
    dry_run=False – wykonuje scalanie
    """
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
        # Wybierz produkt główny (możesz zmienić kryterium)
        # Kryterium: produkt z największą ilością zdjęć? Albo z największym stanem?
        main_product = max(products, key=lambda p: p.stock_quantity)
        others = [p for p in products if p != main_product]

        print(f"\n📦 Grupa: {main_product.brand} {main_product.name} (ID głównego: {main_product.id})")
        print(f"   Duplikaty: {', '.join(str(p.id) for p in others)}")
        print(f"   Stan magazynowy głównego: {main_product.stock_quantity}")
        print(f"   Suma stanów duplikatów: {sum(p.stock_quantity for p in others)}")

        if dry_run:
            continue

        with transaction.atomic():
            # Zsumuj stany
            total_stock = main_product.stock_quantity + sum(p.stock_quantity for p in others)
            main_product.stock_quantity = total_stock
            main_product.save()

            # Przenieś OrderItem
            for other in others:
                order_items = OrderItem.objects.filter(product=other)
                for item in order_items:
                    item.product = main_product
                    item.save()
                # Przenieś Sale
                sales = Sale.objects.filter(product=other)
                for sale in sales:
                    sale.product = main_product
                    sale.save()
                # Usuń duplikat
                other.delete()
                total_merged += 1

            print(f"   ✅ Scalono. Nowy stan magazynowy: {total_stock}")

    if dry_run:
        print(f"\n🔍 Znaleziono {total_groups} grup duplikatów. Uruchom z dry_run=False aby scalić.")
    else:
        print(f"\n✅ Scalono {total_merged} produktów.")

if __name__ == "__main__":
    # Najpierw uruchom w trybie podglądu:
    merge_products(dry_run=True)
    # Jeśli wyniki są OK, zmień na dry_run=False i uruchom ponownie.