"""Human-reviewable, entirely offline supplier quotation package.

This is neither an accepted order nor a Shopware import schema.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from .recipe import validate_recipe
from .shopping_export import shopping_items
from .supplier_evidence import audit_offers


def _safe_csv(value: Any) -> Any:
    # Mitigate formula execution in spreadsheet tools, including whitespace prefixed formulas.
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
        return "'" + value
    return value


def _safe_markdown(value: Any) -> str:
    # Supplier-sourced data must not inject a Markdown table row or clickable markup.
    return str(value).replace('\\', '&#92;').replace('|', '&#124;').replace('\r', ' ').replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')


def build_rfq(recipe: dict[str, Any], catalog: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_recipe(recipe)
    evidence = audit_offers(recipe, catalog)
    items = shopping_items(recipe)
    if len(items) != len(evidence['rows']):
        raise ValueError('Supplier evidence and recipe positions diverged')
    rows = []
    for item, offer in zip(items, evidence['rows']):
        if item['name'] != offer['ingredient'] or item['required_g'] != offer['required_g']:
            raise ValueError('Supplier evidence and recipe order diverged')
        kind = offer['offer_type']
        row = {
            'category': item['category'],
            'ingredient': item['name'],
            'required_g': item['required_g'],
            'whole_grain_required': item['whole_grain_required'],
            'status': 'DOCUMENTED_OFFER_RECONFIRM' if kind != 'UNRESOLVED' else 'SUPPLIER_MAPPING_REQUIRED',
            'offer_type': kind,
            'supplier_sku': offer.get('supplier_sku'),
            'requested_g': offer.get('requested_g'),
            'pack_g': offer.get('pack_g'),
            'pack_count': offer.get('quantity'),
            'surplus_g': offer.get('surplus_g'),
            'source_url': offer.get('source_url'),
            'source_reviewed_on': offer.get('reviewed_on'),
            'notes': offer['reason'],
        }
        if kind == 'VARIABLE_WEIGHT' and row['pack_count'] is not None:
            raise ValueError('Variable weight is not a fixed-pack purchase')
        if kind == 'FIXED_PACK' and row['pack_count'] is None:
            raise ValueError('Fixed-pack offer missing pack count')
        rows.append(row)
    documented = sum(row['offer_type'] != 'UNRESOLVED' for row in rows)
    unresolved = len(rows) - documented
    warnings = [
        'REQUEST FOR QUOTATION ONLY. No purchase order, payment or checkout authorization.',
        'Merchant must reconfirm SKU, pack size/increment, availability, shipping and final prices.',
        'Eight (or more/fewer as catalog changes) unresolved lines require manual sourcing; do not silently drop them.',
        'No Shopware product IDs are asserted; file is NOT a native Shopware order import.',
        'Uncrushed/whole grain is mandatory for all malt lines.',
        'No customer contact details are included; agree delivery/payment terms separately.',
    ]
    doc = {
        'format': 'homebrew-as-code/supplier-order-request-v1',
        'document_type': 'REQUEST_FOR_QUOTATION',
        'order_submitted': False, 'payment_authorized': False,
        'supplier': evidence['supplier'], 'source_catalog_reviewed_on': evidence['reviewed_on'],
        'recipe': {'id': recipe['recipe']['id'], 'name': recipe['recipe']['name'], 'version': recipe['recipe']['version']},
        'currency': None, 'total_price': None,
        'positions': rows,
        'supplier_action_requested': 'Please quote availability, current unit/total prices, shipping and fulfillment for all positions; suggest alternatives for unresolved entries. Do not place an order without customer confirmation.',
        'warnings': warnings,
    }
    report = {
        'format': 'homebrew-as-code/supplier-order-request-report-v1',
        'order_submitted': False, 'ready_to_send_as_rfq': True,
        'ready_to_order': False, 'shopware_cart_ready': False,
        'position_count': len(rows), 'documented_offer_count': documented,
        'unresolved_count': unresolved,
        'variable_weight_count': sum(r['offer_type'] == 'VARIABLE_WEIGHT' for r in rows),
        'fixed_pack_count': sum(r['offer_type'] == 'FIXED_PACK' for r in rows),
        'unresolved_ingredients': [r['ingredient'] for r in rows if r['offer_type'] == 'UNRESOLVED'],
        'manual_review': warnings,
    }
    return doc, report


def render_rfq(recipe: dict[str, Any], catalog: dict[str, Any]) -> dict[str, str]:
    doc, report = build_rfq(recipe, catalog)
    columns = ['category', 'ingredient', 'required_g', 'whole_grain_required', 'status',
               'offer_type', 'supplier_sku', 'requested_g', 'pack_g', 'pack_count',
               'surplus_g', 'source_url', 'source_reviewed_on', 'notes']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=columns, delimiter=';', lineterminator='\n')
    writer.writeheader()
    for row in doc['positions']:
        writer.writerow({key: _safe_csv('' if row.get(key) is None else row[key]) for key in columns})
    markdown = [
        '# Unverbindliche Angebotsanfrage / Request for quotation', '',
        '**KEINE BESTELLUNG. Keine Zahlungs- oder Kaufautorisierung.**', '',
        f"Rezept: {_safe_markdown(doc['recipe']['name'])} (v{_safe_markdown(doc['recipe']['version'])})",
        f"Lieferant: {_safe_markdown(doc['supplier'])}",
        f"Produktquellen zuletzt geprüft: {_safe_markdown(doc['source_catalog_reviewed_on'])}",
        '', 'Bitte prüfen Sie alle 15 Positionen, bestätigen Sie die lieferbaren Artikel,',
        'Preise und Versandkosten und bieten Sie für offene Positionen Alternativen an.',
        'Eine Bestellung darf erst nach ausdrücklicher Freigabe erfolgen.', '',
        '| Rohstoff | Bedarf (g) | Artikel-Nr. | Bestellmenge | Status | Quelle |',
        '|---|---:|---|---|---|---|',
    ]
    for row in doc['positions']:
        if row['offer_type'] == 'VARIABLE_WEIGHT':
            qty = f"{row['requested_g']:g} g, variable Gewichtsmenge (keine Packung)"
        elif row['offer_type'] == 'FIXED_PACK':
            qty = f"{row['pack_count']} × {row['pack_g']:g} g"
        else:
            qty = 'Offen – bitte anbieten'
        cols = [row['ingredient'], f"{row['required_g']:g}", row['supplier_sku'] or '–',
                qty, row['status'], row['source_url'] or '–']
        markdown.append('| ' + ' | '.join(_safe_markdown(x) for x in cols) + ' |')
    markdown.extend(['', f"**{report['documented_offer_count']}/{report['position_count']}** dokumentierte Angebote; "
                     f"**{report['unresolved_count']}** offene Positionen.", '',
                     'Alle ungeschroteten Malze bitte ausdrücklich in ungeschroteter Ausführung anbieten.',
                     'Für dokumentierte Artikel Lieferbarkeit, Mengenstaffelung und Preise neu bestätigen.',
                     'Diese CSV/JSON ist kein natives Shopware-Importformat.',
                     'Kontaktdaten, Rechnungs-/Lieferadresse und Zahlungsinformationen gehören nicht in diesen Export.', ''])
    return {
        '.rfq.json': json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
        '.rfq.csv': stream.getvalue(),
        '.rfq.md': '\n'.join(markdown),
        '.rfq-report.json': json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
    }
