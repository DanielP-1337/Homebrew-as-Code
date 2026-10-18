"""Offline supplier RFQ and Shopware 6 Store API cart preview.

No merchant endpoints, authentication, prices or order submission.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
from pathlib import Path
from typing import Any

from .recipe import load_recipe, validate_recipe

HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")


def shopping_items(recipe: dict[str, Any]) -> list[dict[str, Any]]:
    validate_recipe(recipe)
    items = []
    for malt in recipe['fermentables']:
        items.append({'category': 'malt', 'name': malt['name'], 'required_g': malt['amount_g'], 'whole_grain_required': True})
    for addition in recipe['boil'].get('additions', []):
        category = 'hop' if 'alpha_acid_percent' in addition else 'other'
        items.append({'category': category, 'name': addition['ingredient'], 'required_g': addition['amount_g'], 'whole_grain_required': False})
    yeast = recipe.get('yeast')
    if isinstance(yeast, dict) and yeast.get('name') and yeast.get('amount_g'):
        items.append({'category': 'yeast', 'name': yeast['name'], 'required_g': yeast['amount_g'], 'whole_grain_required': False})
    # Salt specifications are in grams, with no specific vendor SKU inferred.
    for key, amount in recipe['water']['salts_g'].items():
        if amount > 0:
            items.append({'category': 'water_salt', 'name': key, 'required_g': amount, 'whole_grain_required': False})
    return items


def build_request(recipe: dict[str, Any], *, supplier: str = 'braupartner.de',
                  catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """A vendor-neutral request for quotation, not a Shopware order."""
    catalog = catalog or {}
    if not isinstance(catalog, dict):
        raise ValueError('catalog must be a mapping')
    results = []
    for item in shopping_items(recipe):
        match = catalog.get(item['name'], {})
        if not isinstance(match, dict):
            raise ValueError('catalog entries must be mappings')
        sku = match.get('sku')
        product_id = match.get('shopware_product_id')
        pack_g = match.get('pack_g')
        if sku is not None and (not isinstance(sku, str) or not sku.strip()):
            raise ValueError('sku must be nonempty text')
        if product_id is not None and (not isinstance(product_id, str) or not HEX32.fullmatch(product_id)):
            raise ValueError('shopware_product_id must be a 32-character hexadecimal Shopware product ID')
        if pack_g is not None and (isinstance(pack_g, bool) or not isinstance(pack_g, (int, float)) or not math.isfinite(pack_g) or pack_g <= 0):
            raise ValueError('pack_g must be a positive finite number')
        result = {**item, 'supplier_sku': sku, 'shopware_product_id': product_id,
                  'pack_g': pack_g,
                  'purchase_quantity': math.ceil(item['required_g'] / pack_g) if pack_g else None,
                  'needs_catalog_resolution': not all((sku, product_id, pack_g))}
        results.append(result)
    return {'format': 'homebrew-as-code/supplier-rfq-v1', 'supplier': supplier,
            'recipe_name': recipe['recipe']['name'], 'recipe_version': recipe['recipe']['version'],
            'status': 'REQUEST_FOR_QUOTATION_ONLY', 'order_submitted': False,
            'currency': None, 'price_total': None, 'items': results,
            'manual_review': ['Supplier must confirm SKU, pack size, availability, prices and shipping',
                              'Do not treat this document as a Shopware native order import',
                              'Customer must expressly approve checkout and payment']}


def build_shopware_cart_preview(request: dict[str, Any]) -> dict[str, Any]:
    """Prepare a Store API cart line-item *example*, never dispatch it.

    Refuse to emit a partial cart: every item needs an exact merchant product ID
    and a known purchasable package size.
    """
    rows = request['items']
    if not rows or any(x['needs_catalog_resolution'] for x in rows):
        return {'ready': False, 'request': None,
                'reason': 'All items require verified merchant product IDs, SKUs and pack sizes'}
    lines = []
    for i, row in enumerate(rows):
        lines.append({'type': 'product', 'referencedId': row['shopware_product_id'],
                      'quantity': row['purchase_quantity']})
    return {'ready': True, 'request': {'lineItems': lines},
            'method': 'POST', 'path': '/store-api/checkout/cart/line-item',
            'transmitted': False, 'checkout_or_order_supported': False}


def _csv_safe(value: object) -> object:
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
        return '\'' + value
    return value


def export_texts(recipe: dict[str, Any], *, catalog: dict[str, Any] | None = None) -> tuple[str, str, str]:
    rfq = build_request(recipe, catalog=catalog)
    cart = build_shopware_cart_preview(rfq)
    output = io.StringIO(newline='')
    writer = csv.writer(output, delimiter=';', lineterminator='\n')
    writer.writerow(['category','name','required_g','whole_grain_required','supplier_sku','pack_g','purchase_quantity','shopware_product_id'])
    for x in rfq['items']:
        writer.writerow([_csv_safe(v) for v in [x['category'], x['name'], x['required_g'], x['whole_grain_required'],
                         x['supplier_sku'] or '', x['pack_g'] if x['pack_g'] is not None else '',
                         x['purchase_quantity'] if x['purchase_quantity'] is not None else '',
                         x['shopware_product_id'] or '']])
    return (json.dumps(rfq, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
            output.getvalue(),
            json.dumps(cart, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def export_file(path: str, *, catalog_path: str | None = None) -> tuple[str, str, str]:
    import yaml
    catalog = yaml.safe_load(Path(catalog_path).read_text(encoding='utf-8')) if catalog_path else None
    return export_texts(load_recipe(path), catalog=catalog)
