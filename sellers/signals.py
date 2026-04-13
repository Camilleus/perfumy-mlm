from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings


@receiver(post_save, sender='orders.Order')
def handle_new_order(sender, instance, created, **kwargs):
    if not created:
        return

    # Sprawdź czy zamówienie miało kod polecenia
    referral_code = getattr(instance, '_referral_code', None)
    if not referral_code:
        return

    try:
        from sellers.models import Seller, Referral
        referrer = Seller.objects.get(referral_code=referral_code)

        # Zwiększ licznik poleceń
        referrer.referral_count += 1
        referrer.credit += 20
        old_level = referrer.level
        referrer.save()  # save() automatycznie ustawia nowy level

        # Zapisz polecenie
        Referral.objects.create(
            referrer=referrer,
            referred_email=instance.email,
            discount_used=True,
            credit_awarded=True,
        )

        # Email gdy ktoś zbliża się do progu
        next_level = referrer.get_next_level_info()
        if next_level:
            remaining = next_level['target'] - next_level['current']
            if remaining in [1, 2]:
                try:
                    send_mail(
                        subject=f'Jesteś blisko poziomu {next_level["next"]}! 🎯',
                        message=f'''Hej {referrer.user.username}!

Właśnie ktoś skorzystał z Twojego kodu polecenia.

Brakuje Ci tylko {remaining} {'polecenia' if remaining == 1 else 'poleceń'} do poziomu {next_level["next"]}!

{'Zdobędziesz -20 zł na każde zamówienie!' if next_level["next"] == 'Ambasador' else 'Zdobędziesz -5% na wszystko + early access!'}

Udostępnij swój link: {settings.SITE_URL}/rejestracja/{referrer.referral_code}/

Przystanek PsikPsik
''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[referrer.user.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass

        # Email gdy awans na nowy poziom
        if referrer.level != old_level:
            try:
                send_mail(
                    subject=f'Awansowałeś na poziom {referrer.get_level_display()}! 🎉',
                    message=f'''Hej {referrer.user.username}!

Gratulacje! Awansowałeś na poziom {referrer.get_level_display()}!

{'Twoja nagroda: -20 zł na każde zamówienie!' if referrer.level == 'ambasador' else 'Twoja nagroda: -5% na wszystko + early access do nowych dostaw!'}

Zaloguj się i sprawdź swój panel:
{settings.SITE_URL}/panel/

Przystanek PsikPsik
''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[referrer.user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

    except Exception:
        pass