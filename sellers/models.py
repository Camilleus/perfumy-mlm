import random
import string
from django.contrib.auth.models import User
from django.db import models


def generate_referral_code(user):
    name_part = user.username[:5].upper()
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{name_part}-{random_part}"


class Seller(models.Model):
    LEVEL_CHOICES = [
        ('starter', '🌱 Starter'),
        ('ambasador', '🥈 Ambasador'),
        ('vip', '🥇 VIP'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Kod polecenia')
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Kredyt (zł)')
    referral_count = models.IntegerField(default=0, verbose_name='Liczba poleceń')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='starter', verbose_name='Poziom')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            code = generate_referral_code(self.user)
            while Seller.objects.filter(referral_code=code).exists():
                code = generate_referral_code(self.user)
            self.referral_code = code
        if self.referral_count >= 10:
            self.level = 'vip'
        elif self.referral_count >= 3:
            self.level = 'ambasador'
        else:
            self.level = 'starter'
        super().save(*args, **kwargs)

    def get_next_level_info(self):
        if self.level == 'starter':
            return {'next': 'Ambasador', 'current': self.referral_count, 'target': 3}
        elif self.level == 'ambasador':
            return {'next': 'VIP', 'current': self.referral_count, 'target': 10}
        return None

    def get_discount(self):
        if self.level == 'vip':
            return '5%'
        elif self.level == 'ambasador':
            return '-20 zł'
        return None

    def __str__(self):
        return f"{self.user.username} ({self.get_level_display()})"

    class Meta:
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'


class Referral(models.Model):
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