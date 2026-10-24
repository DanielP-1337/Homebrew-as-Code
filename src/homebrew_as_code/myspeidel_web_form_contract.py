"""Offline inspection of a captured MySpeidel HTML recipe form POST.

No HTTP clients, browser cookies, or authentication are used by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qsl

MAX_INPUT_BYTES = 2_000_000
GROUPS = ('recipe', 'malts_to_recipe', 'hops_to_recipe', 'ingredients_to_recipe',
          'yeasts_to_recipe', 'fermentation_hops_to_recipe',
          'fermentation_ingredients_to_recipe', 'fermentations_to_recipe',
          'maturations_to_recipe')
GROUP_RE = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*)(?:\[|$)')
INDEXED_RE = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*)\[([^]]+)\](?:\[([^]]+)\])?\[([^]]+)\]$')
SINGLE_INDEX_RE = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*)\[([^]]+)\]\[([^]]+)\]$')
SENSITIVE_KEY_RE = re.compile(r'token|csrf|auth|password|secret|cookie|session|nonce|signature|key', re.I)
ID_FIELDS = {'malt_id', 'hop_id', 'ingredient_id', 'yeast_id'}


def _read_form(path: Path) -> bytes:
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError('Form source missing or exceeds byte limit')
    data = path.read_bytes()
    if len(data) > MAX_INPUT_BYTES or b'\x00' in data:
        raise ValueError('Invalid or oversized form source')
    return data.strip()


def _entry_group(key: str) -> str:
    match = GROUP_RE.match(key)
    return match.group(1) if match else '(unclassified)'


def inspect_form(data: bytes) -> dict:
    """Summarize URL encoded data without exporting arbitrary form values."""
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError('Form too large')
    decoded = data.decode('utf-8', errors='strict')
    pairs = parse_qsl(decoded, keep_blank_values=True, encoding='utf-8', errors='strict')
    if not pairs or not any(k.startswith('recipe[') for k, _ in pairs):
        raise ValueError('Expected a MySpeidel recipe form POST')
    group_counts: dict[str, dict] = defaultdict(lambda: {'fields': 0, 'nonempty': 0})
    duplicates = Counter(k for k, _ in pairs)
    used: dict[str, dict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    recipe_values: dict[str, str] = {}
    for key, value in pairs:
        if not key or len(key) > 300 or len(value) > 20000:
            raise ValueError('Unexpected form field length')
        group = _entry_group(key)
        group_counts[group]['fields'] += 1
        if value:
            group_counts[group]['nonempty'] += 1
        if group == 'recipe' and key.startswith('recipe[') and key.endswith(']'):
            field = key[7:-1]
            if '[' not in field and not SENSITIVE_KEY_RE.search(field):
                recipe_values[field] = value
        # Preserve all indexed rows, then report only those with a populated ID.
        match = INDEXED_RE.fullmatch(key)
        if match and match.group(1) in GROUPS:
            base, idx, inner_idx, field = match.groups()
            if not idx.isdecimal() or (inner_idx is not None and not inner_idx.isdecimal()):
                continue
            if SENSITIVE_KEY_RE.search(field):
                continue
            index = f'{idx}/{inner_idx}' if inner_idx is not None else idx
            used[base][index][field] = value
    ingredients = []
    for group in GROUPS:
        if group == 'recipe':
            continue
        for idx, row in sorted(used[group].items(), key=lambda item: tuple(int(x) for x in item[0].split('/'))):
            id_field = next((f for f in ID_FIELDS if row.get(f)), None)
            if id_field:
                ingredients.append({'group': group, 'index': idx, 'id_field': id_field,
                                    'id_value': row[id_field],
                                    'amount': row.get('amount', ''),
                                    'acid': row.get('acid', '')})
    result = {
        'format': 'homebrew-as-code/myspeidel-web-form-contract-v1',
        'source': 'offline_html_form_post',
        'form_sha256': hashlib.sha256(data).hexdigest(),
        'field_count': len(pairs),
        'nonempty_count': sum(bool(value) for _, value in pairs),
        'empty_count': sum(not value for _, value in pairs),
        'group_counts': dict(sorted(group_counts.items())),
        'duplicate_field_names': {k: v for k, v in sorted(duplicates.items()) if v > 1 and not SENSITIVE_KEY_RE.search(k)},
        'recipe_fields': {k: recipe_values[k] for k in (
            'name', 'style', 'machine_type_id', 'water_type_id',
            'water_amount_start', 'water_amount_addition', 'water_plato',
            'boiling_duration') if k in recipe_values},
        'ingredient_rows': ingredients,
        'form_contains_references_object': any(k == 'references' or k.startswith('references[') for k, _ in pairs),
        'form_contains_recipe_uuid': any(k == 'recipe[uuid]' for k, _ in pairs),
        'notes': [
            'Form ingredient IDs are not assumed to match Cloud API UUIDs.',
            'This form POST is not a Cloud API PUT payload.',
            'A 200 HTTP response alone does not prove persistence.',
        ],
    }
    return result


def compare_cloud_backup(report: dict, backup: dict) -> dict:
    recipe = backup.get('recipe')
    if not isinstance(recipe, dict):
        raise ValueError('Expected a roundtrip backup containing recipe object')
    fields = report['recipe_fields']
    checked = {}
    for key in ('name', 'style', 'water_plato', 'water_amount_start',
                'water_amount_addition', 'boiling_duration'):
        if key in fields and key in recipe:
            checked[key] = {'form': fields[key], 'cloud': recipe[key],
                            'string_equal': str(recipe[key]) == fields[key]}
    return {
        'recipe_fields_compared': checked,
        'cloud_reference_categories': sorted((recipe.get('references') or {}).keys())
        if isinstance(recipe.get('references'), dict) else [],
        'ingredient_id_mapping': 'unverified',
        'note': 'Form numeric IDs and Cloud API reference UUIDs are different domains; no automatic mapping is inferred.',
    }


def _local_path(value: str, *, exists: bool) -> Path:
    path = Path(value).resolve()
    root = Path('.local').resolve()
    if not path.is_relative_to(root) or (exists and not path.is_file()):
        raise ValueError('Inputs and outputs must be under .local')
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline MySpeidel web-form contract inspector')
    parser.add_argument('--form', required=True, help='Raw DevTools View Source POST body in .local')
    parser.add_argument('--report', required=True, help='New JSON report inside .local')
    parser.add_argument('--backup', help='Optional Cloud API recipe backup inside .local')
    args = parser.parse_args(argv)
    try:
        form = _local_path(args.form, exists=True)
        out = _local_path(args.report, exists=False)
        if out.exists():
            raise ValueError('Report already exists; refusing overwrite')
        raw = _read_form(form)
        report = inspect_form(raw)
        if args.backup:
            backup_path = _local_path(args.backup, exists=True)
            backup = json.loads(backup_path.read_text(encoding='utf-8'))
            report['cloud_comparison'] = compare_cloud_backup(report, backup)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('x', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        print('Offline form inspection completed; no HTTP requests or writes to recipes.')
        print(f'Fields: {report["field_count"]}; nonempty: {report["nonempty_count"]}; ingredient rows: {len(report["ingredient_rows"])}')
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f'Web-form inspection stopped: {type(exc).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
