from django.db import models
from products.models import Product
from sellers.models import Seller

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