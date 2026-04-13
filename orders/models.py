from django.db import models
from products.models import Product
from sellers.models import Seller


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Nowe'),
        ('confirmed', 'Potwierdzone'),
        ('shipped', 'Wysłane'),
        ('delivered', 'Dostarczone'),
        ('cancelled', 'Anulowane'),
    ]

    first_name = models.CharField(max_length=100, verbose_name='Imię')
    last_name = models.CharField(max_length=100, verbose_name='Nazwisko')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    address = models.CharField(max_length=200, verbose_name='Ulica i numer')
    city = models.CharField(max_length=100, verbose_name='Miasto')
    postal_code = models.CharField(max_length=10, verbose_name='Kod pocztowy')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Status')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Łączna kwota')
    note = models.TextField(blank=True, verbose_name='Uwagi do zamówienia')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data zamówienia')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Zniżka')

    def __str__(self):
        return f"Zamówienie #{self.pk} – {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = 'Zamówienie'
        verbose_name_plural = 'Zamówienia'
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    class Meta:
        verbose_name = 'Pozycja zamówienia'
        verbose_name_plural = 'Pozycje zamówienia'

class Sale(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.PROTECT, related_name='sales')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seller} - {self.product} - {self.sale_date.date()}"

    class Meta:
        verbose_name = 'Sprzedaż'
        verbose_name_plural = 'Sprzedaże'

class Commission(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.PROTECT, related_name='commissions')
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    level = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seller} - {self.amount} zł - poziom {self.level}"

    class Meta:
        verbose_name = 'Prowizja'
        verbose_name_plural = 'Prowizje'