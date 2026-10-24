"""Offline, evidence-based comparison of MySpeidel web IDs with Cloud UUIDs.

Never promotes coincidental quantities to verified identity mappings.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .myspeidel_web_form_contract import MAX_INPUT_BYTES, _read_form, inspect_form

FORMAT = 'homebrew-as-code/myspeidel-web-cloud-identity-candidates-v1'


def _number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value).replace(',', '.').strip())
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _cloud_occurrences(recipe: dict[str, Any]) -> list[dict[str, Any]]:
    """Find explicit *_uuid references in recipe operations, not catalog definitions."""
    result: list[dict[str, Any]] = []
    kind_fields = {'malt_uuid': 'malts', 'hop_uuid': 'hops',
                   'ingredient_uuid': 'ingredients', 'yeast_uuid': 'yeasts'}

    def visit(node: Any, path: tuple[str, ...]) -> None:
        if isinstance(node, dict):
            for field, kind in kind_fields.items():
                uid = node.get(field)
                if isinstance(uid, str) and uid:
                    # Ignore definitions under references, even nested ones.
                    if 'references' not in path:
                        result.append({
                            'kind': kind, 'uuid': uid, 'amount': node.get('amount'),
                            'acid': node.get('acid'), 'path': '$.' + '.'.join(path),
                        })
            for k, value in node.items():
                if k not in kind_fields:
                    visit(value, (*path, str(k)))
        elif isinstance(node, list):
            for i, value in enumerate(node):
                visit(value, (*path, str(i)))

    visit(recipe, ())
    return result


def inspect_mapping(form_report: dict[str, Any], recipe: dict[str, Any]) -> dict[str, Any]:
    """Produce candidate correspondences; never infer verified identities."""
    if not isinstance(recipe, dict):
        raise ValueError('Cloud recipe must be an object')
    web_rows = form_report.get('ingredient_rows')
    if not isinstance(web_rows, list):
        raise ValueError('Expected report with ingredient_rows')
    cloud_rows = _cloud_occurrences(recipe)
    kinds = {'malts_to_recipe': 'malts', 'hops_to_recipe': 'hops',
             'ingredients_to_recipe': 'ingredients', 'yeasts_to_recipe': 'yeasts',
             'fermentation_hops_to_recipe': 'hops',
             'fermentation_ingredients_to_recipe': 'ingredients'}
    records = []
    per_id: dict[tuple[str, str], list[set[str]]] = defaultdict(list)
    for row in web_rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid ingredient row')
        group = row.get('group')
        kind = kinds.get(group)
        web_id = row.get('id_value')
        if not kind or not isinstance(web_id, str) or not web_id:
            continue
        amount = _number(row.get('amount'))
        acid = _number(row.get('acid'))
        possibilities = []
        for c in cloud_rows:
            if c['kind'] != kind:
                continue
            if amount is None or _number(c['amount']) != amount:
                continue
            # Compare acid only when present on both sides, never treat an
            # absent Cloud acid as a matching 0.
            cloud_acid = _number(c['acid'])
            if acid is not None and cloud_acid is not None and acid != cloud_acid:
                continue
            possibilities.append(c)
        uuids = sorted({item['uuid'] for item in possibilities})
        evidence = ['kind', 'amount'] if amount is not None else ['kind']
        if acid is not None and possibilities and all(_number(c['acid']) == acid for c in possibilities):
            evidence.append('acid')
        state = ('UNRESOLVED' if not uuids else 'AMBIGUOUS' if len(uuids) > 1
                 else 'CANDIDATE')
        records.append({
            'web_group': group, 'web_index': row.get('index'), 'web_id': web_id,
            'web_amount': row.get('amount'), 'web_acid': row.get('acid'),
            'status': state, 'candidate_cloud_uuids': uuids,
            'evidence': evidence,
            'note': 'Candidate only; ingredient identity is not verified by matching quantities.',
        })
        per_id[(kind, web_id)].append(set(uuids))
    # The same web ID appearing in multiple rows must not map to conflicting UUIDs.
    for record in records:
        group = record['web_group']
        key = (kinds[group], record['web_id'])
        occurrence_sets = per_id[key]
        if len(occurrence_sets) > 1:
            common = set.intersection(*occurrence_sets)
            if not common and any(occurrence_sets):
                record['status'] = 'INCONSISTENT'
                record['candidate_cloud_uuids'] = []
            elif common:
                record['candidate_cloud_uuids'] = sorted(common)
                record['status'] = 'CANDIDATE' if len(common) == 1 else 'AMBIGUOUS'
                record['evidence'].append('repeat_web_id_consistency')
    return {
        'format': FORMAT,
        'verified_mapping_count': 0,
        'form_recipe_name': form_report.get('recipe_fields', {}).get('name'),
        'cloud_recipe_name': recipe.get('name'),
        'name_equal': form_report.get('recipe_fields', {}).get('name') == recipe.get('name'),
        'cloud_occurrence_count': len(cloud_rows),
        'web_occurrence_count': len(records),
        'mappings': records,
        'notes': [
            'CANDIDATE is not a verified ID mapping; manual confirmation or authoritative IDs are required.',
            'Quantity and acidity alone are not globally unique ingredient identifiers.',
            'No data was sent to MySpeidel; no source files were modified.',
        ],
    }


def _local_path(raw: str, *, must_exist: bool) -> Path:
    path = Path(raw).resolve()
    root = Path('.local').resolve()
    if not path.is_relative_to(root) or (must_exist and not path.is_file()):
        raise ValueError('All input/output paths must be under .local')
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline web-to-cloud ingredient identity candidate audit')
    parser.add_argument('--form', required=True)
    parser.add_argument('--backup', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args(argv)
    try:
        form = _local_path(args.form, must_exist=True)
        backup_path = _local_path(args.backup, must_exist=True)
        report_path = _local_path(args.report, must_exist=False)
        if report_path.exists():
            raise ValueError('Refusing to overwrite existing report')
        from .myspeidel_put_roundtrip import read_backup
        _, recipe, _ = read_backup(backup_path)
        data = inspect_form(_read_form(form))
        result = inspect_mapping(data, recipe)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open('x', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        print('Offline candidate audit completed; NO HTTP and NO verified identity claims.')
        print(f'Form rows: {result["web_occurrence_count"]}; Cloud rows: {result["cloud_occurrence_count"]}')
        return 0
    except (OSError, ValueError, UnicodeError, TypeError, json.JSONDecodeError) as exc:
        print(f'Identity audit stopped: {type(exc).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
