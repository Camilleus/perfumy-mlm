# orders/shipping.py

SHIPPING_METHODS = {
    'pl': [  # opcje dla Polski
        {
            'id': 'inpost',
            'name': 'InPost Kurier (szybka wysyłka)',
            'cost_pln': 30,
            'free_above_qty': 3,
        },
        {
            'id': 'dhl',
            'name': 'DHL Kurier',
            'cost_pln': 35,
        },
        {
            'id': 'dpd',
            'name': 'DPD Kurier',
            'cost_pln': 35,
        },
        {
            'id': 'gls',
            'name': 'GLS Ekspres (szybka wysyłka)',
            'cost_pln': 40,
        },
    ],
    'intl': [
        {
            'id': 'international',
            'name': 'Wysyłka zagraniczna',
            'cost_pln': 249.95,
            'is_estimate': True,
        },
    ],
}