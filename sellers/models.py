from django.contrib.auth.models import User
from django.db import models

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    sponsor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Sprzedawca'
        verbose_name_plural = 'Sprzedawcy'