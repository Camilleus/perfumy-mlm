from django.db import models
from products.models import Product


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    email = models.EmailField(verbose_name='Email')
    name = models.CharField(max_length=100, verbose_name='Imię')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Ocena')
    comment = models.TextField(verbose_name='Opinia')
    verified_purchase = models.BooleanField(default=False, verbose_name='Zweryfikowany zakup')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} – {self.product.name} ({self.rating}★)"

    class Meta:
        verbose_name = 'Opinia'
        verbose_name_plural = 'Opinie'
        ordering = ['-created_at']