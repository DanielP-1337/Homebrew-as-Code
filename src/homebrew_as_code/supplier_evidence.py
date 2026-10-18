"""Auditable OFFLINE supplier offers; no live price, inventory, API or cart calls."""
from __future__ import annotations

import math
from datetime import date
from typing import Any
from urllib.parse import urlsplit

from .shopping_export import shopping_items


def _positive(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f'{field} must be a finite positive number')
    return float(value)


def _source(url: Any) -> str:
    if not isinstance(url, str):
        raise ValueError('product source_url must be an HTTPS braupartner.de URL')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('braupartner.de', 'www.braupartner.de') or parsed.username or parsed.password or parsed.port or not parsed.path.startswith('/') or parsed.query or parsed.fragment:
        raise ValueError('product source_url must be an HTTPS braupartner.de URL')
    return url


def audit_offers(recipe: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    if source.get('schema_version') != 1 or source.get('supplier') != 'braupartner.de':
        raise ValueError('Expected Braupartner supplier schema version 1')
    reviewed = source.get('reviewed_on')
    try:
        if not isinstance(reviewed, str):
            raise ValueError()
        date.fromisoformat(reviewed)
    except ValueError as exc:
        raise ValueError('reviewed_on must be an ISO date') from exc
    products = source.get('products')
    if not isinstance(products, dict):
        raise ValueError('products mapping required')
    items = shopping_items(recipe)
    if set(products) - {item['name'] for item in items}:
        raise ValueError('Unexpected ingredient in supplier catalog')
    rows = []
    for item in items:
        name, required = item['name'], item['required_g']
        spec = products.get(name, {})
        if not isinstance(spec, dict):
            raise ValueError('Product must be a mapping')
        offer = spec.get('offer')
        packs = spec.get('packs', [])
        if not isinstance(packs, list):
            raise ValueError('packs must be a list')
        if offer is not None and packs:
            raise ValueError('Variable-weight product must not be mislabeled as fixed packs')
        if offer is not None:
            if not isinstance(offer, dict) or offer.get('kind') != 'variable_weight':
                raise ValueError('Unsupported offer kind')
            if item['whole_grain_required'] and offer.get('whole_grain') is not True:
                raise ValueError('Ungeschrotet required')
            minimum = _positive(offer.get('min_g'), 'min_g')
            increment = _positive(offer.get('increment_g'), 'increment_g')
            url = _source(offer.get('source_url'))
            if not isinstance(offer.get('sku'), str) or not offer['sku'].strip():
                raise ValueError('Documented supplier SKU required')
            qty = minimum + math.ceil(max(0, required - minimum) / increment - 1e-10) * increment
            rows.append({'ingredient': name, 'required_g': required, 'offer_type': 'VARIABLE_WEIGHT',
                         'supplier_sku': offer['sku'], 'requested_g': qty, 'surplus_g': qty - required,
                         'source_url': url, 'reviewed_on': reviewed,
                         'cart_mapping_supported': False, 'reason': 'Merchant quantity units must be confirmed before Shopware cart mapping'})
            continue
        verified = []
        for pack in packs:
            if not isinstance(pack, dict):
                raise ValueError('Pack must be a mapping')
            _positive(pack.get('pack_g'), 'pack_g')
            url = _source(pack.get('source_url'))
            if not isinstance(pack.get('sku'), str) or not pack['sku'].strip():
                raise ValueError('Documented supplier SKU required')
            if pack.get('verified') is not True:
                continue
            if item['whole_grain_required'] and pack.get('whole_grain') is not True:
                continue
            count = math.ceil(required / pack['pack_g'])
            verified.append((count * pack['pack_g'] - required, count, pack, url))
        if verified:
            _, count, pack, url = min(verified, key=lambda x:(x[0], x[1]))
            rows.append({'ingredient': name, 'required_g': required, 'offer_type': 'FIXED_PACK',
                         'supplier_sku': pack['sku'], 'pack_g': pack['pack_g'], 'quantity': count,
                         'requested_g': count * pack['pack_g'], 'surplus_g': count * pack['pack_g'] - required,
                         'source_url': url, 'reviewed_on': reviewed, 'cart_mapping_supported': False,
                         'reason': 'Merchant Shopware product ID unknown; checkout forbidden'})
        else:
            rows.append({'ingredient': name, 'required_g': required, 'offer_type': 'UNRESOLVED',
                         'cart_mapping_supported': False, 'reason': 'No verified supplier offer'})
    return {'format': 'homebrew-as-code/supplier-evidence-v1', 'reviewed_on': reviewed,
            'supplier': 'braupartner.de', 'order_submitted': False, 'cart_ready': False,
            'availability_verified_now': False, 'prices_verified_now': False, 'rows': rows}
