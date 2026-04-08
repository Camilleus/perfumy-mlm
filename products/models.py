from django.db import models

class Product(models.Model):
    GENDER_CHOICES = [
        ('M', 'Męskie'),
        ('K', 'Damskie'),
        ('U', 'Unisex'),
    ]

    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    scent_notes = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} - {self.name}"

    class Meta:
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkty'