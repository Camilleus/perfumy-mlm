from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sale, Commission

@receiver(post_save, sender=Sale)
def calculate_commissions(sender, instance, created, **kwargs):
    if not created:
        return

    seller = instance.seller
    level = 1

    while seller and level <= 3:
        commission_amount = instance.total_amount * (seller.commission_rate / 100)
        Commission.objects.create(
            seller=seller,
            sale=instance,
            amount=commission_amount,
            level=level,
        )
        seller = seller.sponsor
        level += 1