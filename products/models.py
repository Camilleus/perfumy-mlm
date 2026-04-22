from django.db import models
from django.utils.text import slugify

class Product(models.Model):
    GENDER_CHOICES = [
        ('M', 'Męskie'),
        ('K', 'Damskie'),
        ('U', 'Unisex'),
    ]
    CATEGORY_CHOICES = [
        ('floral', 'Kwiatowe'),
        ('woody', 'Drzewne'),
        ('fresh', 'Świeże'),
        ('oriental', 'Orientalne'),
        ('citrus', 'Cytrusowe'),
    ]
    CONCENTRATION_CHOICES = [
        ('edt', 'EDT'),
        ('edp', 'EDP'),
        ('parfum', 'Parfum'),
    ]
    INTENSITY_CHOICES = [
        ('light', 'Delikatna i świeża'),
        ('strong', 'Mocna i wieczorowa'),
    ]
    OCCASION_CHOICES = [
        ('daily', 'Na co dzień'),
        ('special', 'Specjalne wyjścia'),
    ]

    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    concentration = models.CharField(max_length=10, choices=CONCENTRATION_CHOICES, default='edp')
    scent_notes = models.CharField(max_length=300, blank=True)
    intensity = models.CharField(max_length=10, choices=INTENSITY_CHOICES, blank=True)
    occasion = models.CharField(max_length=10, choices=OCCASION_CHOICES, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    # faq_json = models.TextField(blank=True, default='', verbose_name='FAQ (JSON)')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} - {self.name}"

    class Meta:
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkty'