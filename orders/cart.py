class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        pid = str(product.pk)
        if pid not in self.cart:
            self.cart[pid] = {
                'pk': pid,
                'name': product.name,
                'brand': product.brand,
                'slug': product.slug,
                'price': str(product.price),
                'quantity': 0,
                'image': str(product.image) if product.image else None,
            }
        self.cart[pid]['quantity'] += quantity
        self.save()

    def remove(self, product_id):
        pid = str(product_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def save(self):
        self.session.modified = True

    def get_items(self):
        return self.cart.values()

    def get_total(self):
        from decimal import Decimal
        return round(sum(Decimal(item["price"]) * item["quantity"] for item in self.cart.values()), 2)

    def count(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def clear(self):
        del self.session['cart']
        self.save()

    def decrease(self, product_id):
        pid = str(product_id)
        if pid in self.cart:
            if self.cart[pid]['quantity'] > 1:
                self.cart[pid]['quantity'] -= 1
            else:
                del self.cart[pid]
            self.save()