"""Offline canonical ingredient reference investigation for MySpeidel.

No authentication, network requests, or PUTs. Reference candidates are never
advertised as safe for a live write: a shared ingredient may still be updated.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from .myspeidel_put_roundtrip import check_private, digest, private_file, read_backup, write_new

CATEGORIES = ('water_types', 'hops')


def catalog_get_paths(spec: dict[str, Any]) -> list[dict[str, str]]:
    """List *documented* GET routes potentially related to ingredient catalogs."""
    paths = spec.get('paths', {})
    if not isinstance(paths, dict):
        raise ValueError('Invalid OpenAPI paths')
    result = []
    for path, methods in sorted(paths.items()):
        if not isinstance(path, str) or not isinstance(methods, dict) or 'get' not in methods:
            continue
        operation = methods['get']
        words = (path + ' ' + str(operation.get('operationId', '')) if isinstance(operation, dict) else path).lower()
        if any(term in words for term in ('water', 'hop', 'ingredient', 'catalog', 'reference')):
            result.append({'method': 'GET', 'path': path})
    return result


def _records(catalog: dict[str, Any], category: str) -> dict[str, dict[str, Any]]:
    """Require explicit category-to-UUID maps; do not guess vendor response shapes."""
    section = catalog.get(category)
    if not isinstance(section, dict):
        raise ValueError(f'Missing canonical category: {category}')
    if any(not isinstance(key, str) or not isinstance(value, dict) for key, value in section.items()):
        raise ValueError(f'Invalid canonical category: {category}')
    return section


def resolve(recipe: dict[str, Any], catalog: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fill null names only with exact-UUID canonical names; never change other fields.

    Any other discrepancy is reported by counts, not silently resolved. The
    resulting payload is an offline candidate, NEVER a proven read-only PUT.
    """
    candidate = copy.deepcopy(recipe)
    references = candidate.get('references')
    if not isinstance(references, dict):
        raise ValueError('Recipe references missing')
    report: dict[str, Any] = {}
    for category in CATEGORIES:
        incoming = references.get(category)
        canonical = _records(catalog, category)
        if not isinstance(incoming, dict):
            raise ValueError(f'Recipe reference category missing: {category}')
        replaced = 0
        conflicts = 0
        missing = 0
        for uuid, record in incoming.items():
            if not isinstance(uuid, str) or not isinstance(record, dict):
                raise ValueError(f'Invalid recipe reference entry: {category}')
            source = canonical.get(uuid)
            if source is None:
                missing += 1
                continue
            if not isinstance(source, dict):
                raise ValueError('Invalid canonical reference entry')
            name = source.get('name')
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Canonical reference name missing or blank')
            for key in set(record).intersection(source) - {'name'}:
                if record[key] != source[key]:
                    conflicts += 1
            if record.get('name') is None:
                record['name'] = name
                replaced += 1
            elif record['name'] != name:
                conflicts += 1
        report[category] = {'resolved_null_names': replaced, 'missing_canonical_records': missing,
                            'different_existing_fields': conflicts,
                            'record_count': len(incoming)}
    return candidate, report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Offline MySpeidel canonical reference investigation; no HTTP')
    p.add_argument('--spec', help='Inspect documented GET catalog routes in local OpenAPI')
    p.add_argument('--backup', help='Private recipe backup under .local')
    p.add_argument('--catalog', help='Explicit UUID-keyed canonical reference export under .local')
    p.add_argument('--report', required=True, help='Fresh .local report path')
    p.add_argument('--candidate', help='Optional fresh .local candidate payload file')
    a = p.parse_args(argv)
    try:
        if bool(a.backup) != bool(a.catalog):
            raise ValueError('--backup and --catalog must be provided together')
        if not a.spec and not a.backup:
            raise ValueError('Provide --spec and/or both --backup and --catalog')
        report: dict[str, Any] = {'format': 'homebrew-as-code/myspeidel-canonical-reference-v1',
                                  'offline': True, 'put_authorized': False}
        if a.spec:
            spec_path = private_file(a.spec, must_exist=True)
            if spec_path.stat().st_size > 10_000_000:
                raise ValueError('Oversized OpenAPI specification')
            spec = json.loads(spec_path.read_text(encoding='utf-8'))
            report['documented_get_routes'] = catalog_get_paths(spec)
        if a.backup:
            uuid, original, baseline_sha = read_backup(private_file(a.backup, must_exist=True))
            check_private(original, uuid)
            cat_path = private_file(a.catalog, must_exist=True)
            if cat_path.stat().st_size > 10_000_000:
                raise ValueError('Oversized canonical reference export')
            catalog = json.loads(cat_path.read_text(encoding='utf-8'))
            if not isinstance(catalog, dict):
                raise ValueError('Catalog export must be an object')
            candidate, changes = resolve(original, catalog)
            check_private(candidate, uuid)
            if digest(original) != baseline_sha:
                raise ValueError('Backup integrity mismatch')
            report.update(baseline_sha256=baseline_sha, candidate_sha256=digest(candidate),
                          reference_diagnostics=changes,
                          warning='This candidate can trigger shared-catalog UPDATEs; no PUT support')
            if a.candidate:
                write_new(private_file(a.candidate), candidate)
        elif a.candidate:
            raise ValueError('--candidate requires backup and catalog')
        write_new(private_file(a.report), report)
        print('Offline inspection completed; no HTTP requests or recipe writes.')
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        # Avoid leaking private filenames and catalog values in error text.
        print('Canonical reference inspection stopped: ' + type(exc).__name__)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
