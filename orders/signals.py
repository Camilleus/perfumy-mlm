from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
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

    send_mail(
        subject=f'Nowa sprzedaż – {instance.seller.user.username}',
        message=f'''
Nowa sprzedaż w systemie!

Sprzedawca: {instance.seller.user.username}
Produkt: {instance.product.name}
Ilość: {instance.quantity}
Kwota: {instance.total_amount} zł
Data: {instance.sale_date}
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=True,
    )