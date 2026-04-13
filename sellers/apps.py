from django.apps import AppConfig


class SellersConfig(AppConfig):
    name = 'sellers'

def ready(self):
    import sellers.signals