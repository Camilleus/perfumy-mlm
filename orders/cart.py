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
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())

    def count(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def clear(self):
        del self.session['cart']
        self.save()