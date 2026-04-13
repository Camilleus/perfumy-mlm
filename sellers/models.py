import random
import string
from django.contrib.auth.models import User
from django.db import models


def generate_referral_code(user):
    """Generuje unikalny kod polecenia np. KAMIL-X7K2"""
    name_part = user.username[:5].upper()
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{name_part}-{random_part}"


class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Kod polecenia')
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Kredyt (zł)')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            code = generate_referral_code(self.user)
            while Seller.objects.filter(referral_code=code).exists():
                code = generate_referral_code(self.user)
            self.referral_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'


class Referral(models.Model):
    """Zapis każdego polecenia – kto polecił, kto skorzystał"""
    referrer = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='referrals', verbose_name='Polecający')
    referred_email = models.EmailField(verbose_name='Email poleconego')
    discount_used = models.BooleanField(default=False, verbose_name='Zniżka wykorzystana')
    credit_awarded = models.BooleanField(default=False, verbose_name='Kredyt przyznany')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer} → {self.referred_email}"

    class Meta:
        verbose_name = 'Polecenie'
        verbose_name_plural = 'Polecenia'