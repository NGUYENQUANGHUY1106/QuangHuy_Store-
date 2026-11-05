from decimal import Decimal
from .models import ShippingMethod

DEFAULT_METHODS = {
    'standard': {'name': 'Tiêu chuẩn', 'fee': Decimal('30000'), 'free_from': Decimal('999000'), 'eta_min': 2, 'eta_max': 5},
    'express': {'name': 'Hỏa tốc', 'fee': Decimal('60000'), 'free_from': Decimal('0'), 'eta_min': 1, 'eta_max': 2},
}

def shipping_options_for(address, subtotal):
    options = []
    methods = list(ShippingMethod.objects.filter(is_active=True).prefetch_related('zones'))
    if not methods:
        for code, data in DEFAULT_METHODS.items():
            fee = Decimal('0') if data['free_from'] and subtotal >= data['free_from'] else data['fee']
            options.append({'code': code, 'name': data['name'], 'fee': fee, 'eta_min': data['eta_min'], 'eta_max': data['eta_max']})
        return options
    for method in methods:
        zones = list(method.zones.filter(is_active=True))
        zone = next((item for item in zones if item.province.lower() == address.province.lower()), None)
        if zones and not zone:
            continue
        fee = method.base_fee + (zone.surcharge if zone else Decimal('0'))
        if method.free_from and subtotal >= method.free_from:
            fee = Decimal('0')
        options.append({'code': method.code, 'name': method.name, 'fee': fee, 'eta_min': method.eta_min_days, 'eta_max': method.eta_max_days})
    return options

def selected_shipping(address, subtotal, code):
    return next((item for item in shipping_options_for(address, subtotal) if item['code'] == code), None)
