"""Offline supplier catalogue resolution. Never calls a storefront or submits orders."""
from __future__ import annotations

import math
import re
from typing import Any

from .shopping_export import shopping_items

_HEX32 = re.compile(r'^[0-9a-fA-F]{32}$')


def resolve_catalog(recipe: dict[str, Any], source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Produce 0011-compatible mapping and human-review report.

    Pack candidates are *not* trusted until explicitly marked verified. For a
    single candidate pack size, compute ceil(required/pack); don't infer price,
    availability or merchant product IDs.
    """
    if not isinstance(source, dict) or source.get('schema_version') != 1:
        raise ValueError('supplier catalog schema_version must be 1')
    supplier = source.get('supplier')
    entries = source.get('products')
    if not isinstance(supplier, str) or not supplier.strip() or not isinstance(entries, dict):
        raise ValueError('supplier and products mapping required')
    known = {item['name'] for item in shopping_items(recipe)}
    if set(entries) - known:
        raise ValueError('catalog contains unknown recipe ingredient names')
    mapping: dict[str, Any] = {}
    rows = []
    for item in shopping_items(recipe):
        name = item['name']
        spec = entries.get(name)
        if spec is None:
            rows.append({'ingredient': name, 'required_g': item['required_g'], 'status': 'UNMAPPED', 'reasons': ['No product mapping']})
            continue
        if not isinstance(spec, dict):
            raise ValueError(f'{name}: product mapping must be an object')
        packs = spec.get('packs', [])
        if not isinstance(packs, list):
            raise ValueError(f'{name}: packs must be a list')
        choices = []
        for p in packs:
            if not isinstance(p, dict):
                raise ValueError(f'{name}: pack must be a mapping')
            mass = p.get('pack_g')
            if isinstance(mass, bool) or not isinstance(mass, (int, float)) or not math.isfinite(mass) or mass <= 0:
                raise ValueError(f'{name}: pack_g must be positive and finite')
            sku = p.get('sku')
            pid = p.get('shopware_product_id')
            if sku is not None and (not isinstance(sku, str) or not sku.strip()):
                raise ValueError(f'{name}: invalid SKU')
            if pid is not None and (not isinstance(pid, str) or not _HEX32.fullmatch(pid)):
                raise ValueError(f'{name}: invalid Shopware product ID')
            verified = p.get('verified', False)
            if not isinstance(verified, bool):
                raise ValueError(f'{name}: verified must be boolean')
            if 'whole_grain' in p and not isinstance(p['whole_grain'], bool):
                raise ValueError(f'{name}: whole_grain must be boolean')
            if item['whole_grain_required'] and p.get('whole_grain') is not True:
                continue
            if verified is not True:
                continue
            count = math.ceil(item['required_g'] / mass)
            choices.append((count * mass - item['required_g'], count, mass, p, count))
        # One package SKU per ingredient, no mixing packaging sizes automatically.
        choices.sort(key=lambda x: (x[0], x[1], x[2]))
        if not choices:
            rows.append({'ingredient': name, 'required_g': item['required_g'], 'status': 'UNRESOLVED', 'reasons': ['No verified package compatible with recipe requirements']})
            continue
        excess, _, mass, chosen, count = choices[0]
        product = {'pack_g': mass}
        if chosen.get('sku'):
            product['sku'] = chosen['sku']
        if chosen.get('shopware_product_id'):
            product['shopware_product_id'] = chosen['shopware_product_id']
        mapping[name] = product
        reasons = []
        if 'sku' not in product:
            reasons.append('Supplier SKU not verified')
        if 'shopware_product_id' not in product:
            reasons.append('Shopware product ID not verified')
        if chosen.get('availability') != 'confirmed':
            reasons.append('Availability not confirmed')
        rows.append({'ingredient': name, 'required_g': item['required_g'], 'status': 'MAPPED' if not reasons else 'REVIEW',
                     'sku': product.get('sku'), 'pack_g': mass, 'quantity': count, 'surplus_g': excess, 'reasons': reasons})
    report = {'format': 'homebrew-as-code/supplier-catalog-report-v1', 'supplier': supplier,
              'status': 'OFFLINE_REVIEW', 'order_submitted': False,
              'cart_ready': bool(rows) and all(r['status'] == 'MAPPED' for r in rows),
              'rows': rows,
              'notes': ['No product pages or merchant IDs were automatically inferred',
                        'Pack selection minimizes surplus for a single SKU per ingredient',
                        'Availability and prices require merchant confirmation',
                        'The generated mapping is input for shopping_cli --catalog, not an order']}
    return mapping, report
