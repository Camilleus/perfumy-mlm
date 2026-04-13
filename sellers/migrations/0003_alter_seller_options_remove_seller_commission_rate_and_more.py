import django.db.models.deletion
from django.db import migrations, models
import random
import string


def generate_codes(apps, schema_editor):
    Seller = apps.get_model('sellers', 'Seller')
    for seller in Seller.objects.all():
        name_part = seller.user.username[:5].upper()
        while True:
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code = f"{name_part}-{random_part}"
            if not Seller.objects.filter(referral_code=code).exists():
                seller.referral_code = code
                seller.save()
                break


class Migration(migrations.Migration):

    dependencies = [
        ('sellers', '0002_seller_is_approved'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='seller',
            options={'verbose_name': 'Użytkownik', 'verbose_name_plural': 'Użytkownicy'},
        ),
        migrations.RemoveField(model_name='seller', name='commission_rate'),
        migrations.RemoveField(model_name='seller', name='is_approved'),
        migrations.RemoveField(model_name='seller', name='sponsor'),
        migrations.AddField(
            model_name='seller',
            name='credit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Kredyt (zł)'),
        ),
        migrations.AddField(
            model_name='seller',
            name='referral_code',
            field=models.CharField(blank=True, max_length=20, verbose_name='Kod polecenia'),
        ),
        migrations.RunPython(generate_codes),
        migrations.AlterField(
            model_name='seller',
            name='referral_code',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='Kod polecenia'),
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referred_email', models.EmailField(max_length=254, verbose_name='Email poleconego')),
                ('discount_used', models.BooleanField(default=False, verbose_name='Zniżka wykorzystana')),
                ('credit_awarded', models.BooleanField(default=False, verbose_name='Kredyt przyznany')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('referrer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referrals', to='sellers.seller', verbose_name='Polecający')),
            ],
            options={'verbose_name': 'Polecenie', 'verbose_name_plural': 'Polecenia'},
        ),
    ]
