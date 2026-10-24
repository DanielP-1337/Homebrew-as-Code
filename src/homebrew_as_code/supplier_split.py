"""Offline, explicit supplier-channel split; no order, checkout or network traffic."""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from .supplier_rfq import build_rfq, _safe_csv, _safe_markdown

# Explicit item-level policy. Unrecognized ingredients MUST NOT silently be sent
# to a supplier; update this mapping after human classification.
CHANNELS = {
    'Pale Ale Malt': 'brewshop',
    'Munich Malt Type II': 'brewshop',
    'CaraMunich II': 'brewshop',
    'Melanoidin Malt': 'brewshop',
    'Chocolate Malt': 'brewshop',
    'Goldings pellets': 'brewshop',
    'Fermentis SafAle S-04': 'brewshop',
    'Mild honey': 'grocery',
    'Ceylon cinnamon sticks': 'grocery',
    'Fresh ginger': 'grocery',
    'Whole cloves': 'grocery',
    'Nutmeg': 'grocery',
    'Orange zest': 'grocery',
    'calcium_chloride_dihydrate': 'water_chemistry',
    'calcium_sulfate_dihydrate': 'water_chemistry',
}

SUPPLIERS = {
    'brewshop': {'display_name': 'Braupartner', 'supplier': 'braupartner.de',
                 'action': 'Request quotation from brewing specialist; verify availability and prices'},
    'grocery': {'display_name': 'Supermarkt / Lebensmittelhandel', 'supplier': None,
                'action': 'Local grocery shopping list; choose food-grade products; no vendor assigned'},
    'water_chemistry': {'display_name': 'Apotheke / Brauwasser-Fachhandel', 'supplier': None,
                        'action': 'Request suitable food-grade compounds with EXACT hydration state; confirm availability and quality'},
}

CHEMICAL_DESCRIPTIONS = {
    'calcium_chloride_dihydrate': 'Calciumchlorid-Dihydrat (CaCl2 · 2 H2O), geeignete Lebensmittelqualität',
    'calcium_sulfate_dihydrate': 'Calciumsulfat-Dihydrat (CaSO4 · 2 H2O), geeignete Lebensmittelqualität',
}


def split_request(recipe: dict[str, Any], catalog: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    original, _ = build_rfq(recipe, catalog)
    rows = original['positions']
    names = [row['ingredient'] for row in rows]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate ingredient names: cannot safely classify')
    unknown = set(names) - set(CHANNELS)
    if unknown:
        raise ValueError('Unclassified recipe ingredients: ' + ', '.join(sorted(unknown)))
    result = {}
    for channel, meta in SUPPLIERS.items():
        selected = []
        for row in rows:
            if CHANNELS[row['ingredient']] != channel:
                continue
            item = dict(row)
            if channel != 'brewshop':
                # A non-specialist shop is NOT asked to quote the Braupartner catalog.
                for key in ('supplier_sku', 'requested_g', 'pack_g', 'pack_count',
                            'surplus_g', 'source_url', 'source_reviewed_on'):
                    item[key] = None
                item['offer_type'] = 'NOT_SOURCED'
                item['status'] = 'LOCAL_PURCHASE_REVIEW' if channel == 'grocery' else 'QUALITY_AND_SOURCE_REVIEW'
                item['notes'] = meta['action']
                if channel == 'water_chemistry':
                    item['purchase_description'] = CHEMICAL_DESCRIPTIONS[item['ingredient']]
            selected.append(item)
        result[channel] = {
            'format': 'homebrew-as-code/supplier-channel-request-v1',
            'document_type': 'REQUEST_FOR_QUOTATION' if channel == 'brewshop' else 'PURCHASE_PLANNING_ONLY',
            'channel': channel, 'supplier': meta['supplier'],
            'display_name': meta['display_name'], 'supplier_action_requested': meta['action'],
            'recipe': original['recipe'], 'positions': selected,
            'order_submitted': False, 'payment_authorized': False, 'total_price': None,
            'shopware_cart_ready': False,
            'manual_review_required': True,
        }
    count = sum(len(x['positions']) for x in result.values())
    if count != len(rows):
        raise ValueError('Supplier split lost a recipe position')
    manifest = {'format': 'homebrew-as-code/supplier-split-report-v1',
                'recipe': original['recipe'], 'total_positions': len(rows),
                'counts': {k: len(v['positions']) for k,v in result.items()},
                'brewshop_documented_offers': sum(x['offer_type'] in ('VARIABLE_WEIGHT','FIXED_PACK') for x in result['brewshop']['positions']),
                'order_submitted': False, 'automatic_checkout_enabled': False,
                'warnings': ['Not a Shopware native import or purchase order',
                             'Confirm supplier stock, price, shipping and product grade before any purchase',
                             'Chemicals: verify food suitability and exact hydrate; pharmacy sourcing is NOT guaranteed']}
    return result, manifest


def render_split(recipe: dict[str, Any], catalog: dict[str, Any]) -> dict[str, str]:
    channels, manifest = split_request(recipe, catalog)
    rendered = {}
    for key, doc in channels.items():
        prefix = f'.{key}'
        rendered[prefix + '.json'] = json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        output = io.StringIO(newline='')
        columns = ['ingredient', 'purchase_description', 'required_g', 'whole_grain_required', 'supplier_sku',
                   'requested_g', 'pack_g', 'pack_count', 'status', 'source_url']
        writer = csv.DictWriter(output, fieldnames=columns, delimiter=';', lineterminator='\n')
        writer.writeheader()
        for row in doc['positions']:
            writer.writerow({col: _safe_csv('' if row.get(col) is None else row[col]) for col in columns})
        rendered[prefix + '.csv'] = output.getvalue()
        lines = [f"# {_safe_markdown(doc['display_name'])} – Einkaufsplanung", '',
                 '**UNVERBINDLICH: Keine Bestellung und keine Zahlungsfreigabe.**', '',
                 f"Rezept: {_safe_markdown(doc['recipe']['name'])} ({_safe_markdown(doc['recipe']['version'])})", '',
                 _safe_markdown(doc['supplier_action_requested']), '',
                 '| Rohstoff | Bedarf (g) | Artikel-Nr. | Bestellmenge | Hinweis |',
                 '|---|---:|---|---|---|']
        for row in doc['positions']:
            if row['offer_type'] == 'VARIABLE_WEIGHT':
                quantity = f"{row['requested_g']:g} g (variable Gewichtsmenge)"
            elif row['offer_type'] == 'FIXED_PACK':
                quantity = f"{row['pack_count']} × {row['pack_g']:g} g"
            else:
                quantity = 'Bedarf lokal beschaffen / anfragen'
            label = row.get('purchase_description') or row['ingredient']
            details = row.get('source_url') or row.get('notes') or ''
            cols = [label, f"{row['required_g']:g}", row.get('supplier_sku') or '–', quantity, details]
            lines.append('| ' + ' | '.join(_safe_markdown(x) for x in cols) + ' |')
        if key == 'brewshop':
            lines += ['', 'Alle Malze ausschließlich ungeschrotet; Artikelnummern, Verfügbarkeit und Preise vorab bestätigen.']
        if key == 'water_chemistry':
            lines += ['', '**Nur für Brauwasser geeignete Qualität.** Hydratform und Reinheit ausdrücklich bestätigen; keine stillschweigende Substitution.']
        rendered[prefix + '.md'] = '\n'.join(lines) + '\n'
    rendered['.split-report.json'] = json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    return rendered
