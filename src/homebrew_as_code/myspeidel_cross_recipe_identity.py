"""Offline cross-recipe corroboration of MySpeidel ingredient identity candidates.

Corroboration is never authoritative proof of ingredient identity. No HTTP.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from .myspeidel_identity_mapping import _local_path, inspect_mapping
from .myspeidel_put_roundtrip import read_backup
from .myspeidel_web_form_contract import _read_form, inspect_form

FORMAT = 'homebrew-as-code/myspeidel-cross-recipe-identity-v1'
GROUP_KINDS = {
    'malts_to_recipe': 'malts', 'hops_to_recipe': 'hops',
    'ingredients_to_recipe': 'ingredients', 'yeasts_to_recipe': 'yeasts',
    'fermentation_hops_to_recipe': 'hops',
    'fermentation_ingredients_to_recipe': 'ingredients',
}
MAX_PAIRS = 100
MAX_MANIFEST_BYTES = 100_000


def analyze_pairs(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate 0020b-shaped reports from distinct UUID-backed recipes.

    Each entry contains recipe_uuid and mapping_report; repeated UUIDs are
    refused, even when corresponding files differ. Incomplete recipe reports
    contribute to diagnostics but cannot count as corroborating evidence.
    """
    if not isinstance(pairs, list) or not 1 <= len(pairs) <= MAX_PAIRS:
        raise ValueError('Expected 1..100 recipe pairs')
    seen = set()
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    summaries = []
    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError('Invalid recipe pair')
        uuid = pair.get('recipe_uuid')
        report = pair.get('mapping_report')
        if not isinstance(uuid, str) or not uuid or uuid in seen:
            raise ValueError('Every recipe must have a distinct UUID')
        seen.add(uuid)
        if not isinstance(report, dict) or not isinstance(report.get('mappings'), list):
            raise ValueError('Invalid 0020b report')
        name_equal = report.get('name_equal') is True
        complete = (name_equal and report.get('web_occurrence_count') ==
                    report.get('cloud_occurrence_count'))
        summaries.append({'recipe_uuid': uuid, 'name_equal': name_equal,
                          'occurrence_counts_equal': report.get('web_occurrence_count') ==
                          report.get('cloud_occurrence_count'),
                          'eligible_for_corroboration': complete})
        for mapping in report['mappings']:
            if not isinstance(mapping, dict):
                raise ValueError('Invalid ingredient mapping')
            kind = GROUP_KINDS.get(mapping.get('web_group'))
            web_id = mapping.get('web_id')
            if kind is None or not isinstance(web_id, str) or not web_id:
                continue
            candidates = mapping.get('candidate_cloud_uuids')
            if not isinstance(candidates, list) or any(not isinstance(x, str) or not x for x in candidates):
                raise ValueError('Invalid candidate UUID list')
            status = mapping.get('status')
            if status not in ('CANDIDATE', 'AMBIGUOUS', 'INCONSISTENT', 'UNRESOLVED'):
                raise ValueError('Unknown candidate state')
            groups[(kind, web_id)].append({
                'recipe_uuid': uuid, 'eligible': complete,
                'status': status, 'candidates': set(candidates),
            })
    identities = []
    for (kind, web_id), occurrences in sorted(groups.items()):
        by_recipe: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for occ in occurrences:
            by_recipe[occ['recipe_uuid']].append(occ)
        evidence = []
        for uid, rows in sorted(by_recipe.items()):
            eligible = all(x['eligible'] for x in rows)
            singleton_sets = [x['candidates'] for x in rows
                              if x['status'] == 'CANDIDATE' and len(x['candidates']) == 1]
            all_candidate = len(singleton_sets) == len(rows)
            unique = set.union(*singleton_sets) if singleton_sets else set()
            consistent = eligible and all_candidate and len(unique) == 1
            evidence.append({'recipe_uuid': uid, 'eligible': eligible,
                             'consistent_singleton': consistent,
                             'candidate_cloud_uuids': sorted(set.union(*(x['candidates'] for x in rows))
                                                             if rows else set()),
                             'occurrences': len(rows)})
        eligible_ev = [x for x in evidence if x['eligible']]
        good = [x for x in eligible_ev if x['consistent_singleton']]
        ids = {x['candidate_cloud_uuids'][0] for x in good}
        if not eligible_ev:
            status = 'INSUFFICIENT_EVIDENCE'
        elif any(not x['consistent_singleton'] for x in eligible_ev):
            status = 'AMBIGUOUS_OR_INCOMPLETE'
        elif len(ids) > 1:
            status = 'CONFLICT'
        elif len(good) >= 2:
            status = 'CROSS_RECIPE_CORROBORATED'
        else:
            status = 'SINGLE_RECIPE_CANDIDATE'
        identities.append({'kind': kind, 'web_id': web_id, 'status': status,
                           'distinct_eligible_recipes': len(eligible_ev),
                           'candidate_cloud_uuids': sorted(ids),
                           'recipe_evidence': evidence})
    return {'format': FORMAT, 'recipe_count': len(summaries), 'recipes': summaries,
            'identities': identities, 'verified_mapping_count': 0,
            'notes': [
                'CROSS_RECIPE_CORROBORATED requires two different recipe UUIDs and consistent singleton candidate mapping.',
                'Corroboration from recipe content is not independent catalogue proof; verified_mapping_count remains zero.',
                'Reusing one recipe with another name, form capture or backup cannot increase evidence.',
                'No HTTP requests or recipe changes were made.',
            ]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline cross-recipe ingredient identity candidate audit')
    parser.add_argument('--manifest', required=True, help='JSON array of {form, backup} in .local')
    parser.add_argument('--report', required=True, help='New JSON output under .local')
    args = parser.parse_args(argv)
    try:
        manifest_path = _local_path(args.manifest, must_exist=True)
        out = _local_path(args.report, must_exist=False)
        if out.exists():
            raise ValueError('Refusing report overwrite')
        if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError('Manifest too large')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if not isinstance(manifest, list) or not 1 <= len(manifest) <= MAX_PAIRS:
            raise ValueError('Expected array of 1..100 form/backup pairs')
        pairs = []
        for entry in manifest:
            if not isinstance(entry, dict) or not isinstance(entry.get('form'), str) or not isinstance(entry.get('backup'), str):
                raise ValueError('Manifest entries require form and backup paths')
            form_path = _local_path(entry['form'], must_exist=True)
            backup_path = _local_path(entry['backup'], must_exist=True)
            uuid, recipe, _ = read_backup(backup_path)
            report = inspect_mapping(inspect_form(_read_form(form_path)), recipe)
            pairs.append({'recipe_uuid': uuid, 'mapping_report': report})
        result = analyze_pairs(pairs)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('x', encoding='utf-8') as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write('\n')
        print('Offline cross-recipe audit completed; no HTTP or recipe writes.')
        print(f'Recipes: {result["recipe_count"]}; identities: {len(result["identities"])}; verified: 0')
        return 0
    except (ValueError, OSError, UnicodeError, TypeError, json.JSONDecodeError) as exc:
        print(f'Cross-recipe audit stopped: {type(exc).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
