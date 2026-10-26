"""Offline POST candidates with explicit experimental creation policy. No HTTP."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
import argparse
import json
from pathlib import Path

from .myspeidel_put_roundtrip import digest, private_file, read_backup, write_new
from .myspeidel_import_builder import KINDS, inspect_create_contract
from .myspeidel_golden_validation import _issues

FORMAT = 'homebrew-as-code/myspeidel-create-candidate-v1'
TOP = ('description', 'comments', 'bitterness', 'color', 'water_specific_gravity',
       'brewing_set_active', 'country', 'machine_type', 'owner', 'brewer', 'schema_version')


def policy_from_backup(recipe):
    """Reviewable test assumptions, not documented server initialization rules."""
    return {'format': 'homebrew-as-code/myspeidel-create-policy-v1',
            'recipe_fields': {k: deepcopy(recipe[k]) for k in TOP},
            'content_version': 1, 'addition_schema_version': 2,
            'yeast_time': '', 'assumptions_accepted': False}


def additions(recipe):
    yield from recipe['mashing']['adds'].get('malts', [])
    for step in recipe['boil']['steps']:
        for kind in ('hops', 'ingredients'):
            yield from step['adds'].get(kind, [])
    yield from recipe['fermentation']['adds'].get('yeasts', [])
    # Process steps also receive fresh identities and participate in dry-run collision checks.
    yield from recipe.get('fermentation', {}).get('steps', [])
    yield from recipe.get('maturation', {}).get('steps', [])


def build_candidate(draft, source, policy, spec):
    if draft.get('format') != 'homebrew-as-code/myspeidel-import-draft-v1':
        raise ValueError('Expected 0020q import draft')
    if digest(draft['candidate']) != draft['report']['candidate_sha256']:
        raise ValueError('Draft digest mismatch')
    if policy.get('format') != 'homebrew-as-code/myspeidel-create-policy-v1' or policy.get('assumptions_accepted') is not True:
        raise ValueError('Review policy and set assumptions_accepted to true for offline preparation')
    if set(policy['recipe_fields']) != set(TOP):
        raise ValueError('Policy must contain exactly the documented recipe_fields')
    for key in ('content_version', 'addition_schema_version'):
        if type(policy[key]) is not int or policy[key] < 1:
            raise ValueError('Policy versions must be positive integers')
    if not isinstance(policy['yeast_time'], str):
        raise ValueError('yeast_time must be text')
    candidate = deepcopy(draft['candidate'])
    if candidate.get('public') != 0 or candidate.get('recipe_type') != 0:
        raise ValueError('Expected private beer recipe draft')
    candidate.update(deepcopy(policy['recipe_fields']))
    if candidate['machine_type'].get('size') != 20:
        raise ValueError('Only reviewed 20 L equipment is supported')
    now = datetime.now(timezone.utc).isoformat()
    candidate.update(uuid=str(uuid4()), parent_uuid=None, created_on=now,
                     update_on=now, content_version=policy['content_version'])
    for row in additions(candidate):
        row.update(uuid=str(uuid4()), creation_date=now, update_on=now,
                   content_version=policy['content_version'], schema_version=policy['addition_schema_version'])
    for index, row in enumerate(candidate['fermentation']['adds'].get('yeasts', []), 1):
        row.update(sorting=index, time=policy['yeast_time'])
    for kind in KINDS:
        for key, minimal in candidate['references'][kind].items():
            obj = source['references'].get(kind, {}).get(key)
            if not obj or obj.get('uuid') != key or obj.get('name') != minimal['name']:
                raise ValueError(f'{kind}: selected catalog identity unavailable in backup: {minimal["name"]}')
            candidate['references'][kind][key] = deepcopy(obj)
    # Keep the POST union verdict, plus concrete per-branch diagnostics.
    contract = inspect_create_contract(spec, candidate)
    schema = spec['paths']['/v1.0/recipe']['post']['requestBody']['content']['application/json']['schema']
    branches = []
    for branch in schema.get('oneOf', [schema]):
        errors, unknown = _issues(spec, branch, candidate, '$')
        branches.append({'schema': branch.get('$ref', 'inline'), 'errors': errors,
                         'unverified_constraints': unknown})
    report = {'offline': True, 'upload_ready': False, 'live_create_verified': False,
              'candidate_sha256': digest(candidate), 'source_sha256': digest(source),
              'draft_sha256': digest(draft), 'policy_sha256': digest(policy),
              'contract': contract, 'branches': branches,
              'source_report': deepcopy(draft['report']),
              'assumptions': ['Client UUIDv4 for recipe and additions; server preservation unverified.',
                              'Null parent, current UTC timestamps and explicit policy versions are experimental.',
                              'Catalog objects reused unchanged; cross-recipe persistence unverified.',
                              'Owner/brewer and equipment must match the intended account and setup.',
                              'No HTTP, no dry-run and no persistence performed.']}
    return {'format': FORMAT, 'candidate': candidate, 'report': report}


def choose_references(template, input_fn=input, output_fn=print):
    """Select one existing identity for each duplicate normalized name."""
    result = deepcopy(template)
    for kind in KINDS:
        grouped = {}
        for obj in result['references'][kind]:
            grouped.setdefault(' '.join(obj['name'].casefold().split()), []).append(obj)
        selected = []
        for rows in grouped.values():
            if len(rows) == 1:
                selected.append(rows[0]); continue
            output_fn(f'{kind}: choose catalog entry')
            for i, row in enumerate(rows, 1):
                output_fn(f'{i}  {row["name"]}  [{row["uuid"]}]')
            answer = input_fn('Select number (Enter cancels): ').strip()
            if not answer:
                raise ValueError('Selection cancelled; no output written')
            if not answer.isdecimal() or not 1 <= int(answer) <= len(rows):
                raise ValueError('Invalid selection; no output written')
            selected.append(rows[int(answer)-1])
        result['references'][kind] = selected
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    policy = sub.add_parser('policy'); policy.add_argument('--backup', required=True)
    select = sub.add_parser('select'); select.add_argument('--template', required=True)
    build = sub.add_parser('build')
    for name in ('backup', 'draft', 'policy', 'spec'):
        build.add_argument('--' + name, required=True)
    for item in (policy, select, build):
        item.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        output = private_file(args.output)
        if output.exists():
            raise ValueError('Output exists; choose a new path')
        if args.command == 'select':
            template = json.loads(private_file(args.template, must_exist=True).read_text(encoding='utf-8'))
            from .myspeidel_import_builder import TEMPLATE_FORMAT
            if template.get('format') != TEMPLATE_FORMAT:
                raise ValueError('Expected import template')
            result = choose_references(template)
        else:
            _, source, _ = read_backup(private_file(args.backup, must_exist=True))
            if args.command == 'policy':
                result = policy_from_backup(source)
            else:
                def local(name):
                    return json.loads(private_file(name, must_exist=True).read_text(encoding='utf-8'))
                result = build_candidate(local(args.draft), source, local(args.policy),
                                         json.loads(Path(args.spec).read_text(encoding='utf-8')))
        write_new(output, result)
        print('Saved offline artifact. NO API requests. NOT upload-ready.')
        if args.command == 'build':
            print('POST union errors:', len(result['report']['contract']['schema_errors']))
            for branch in result['report']['branches']:
                print(branch['schema'], 'errors:', len(branch['errors']),
                      'unverified:', len(branch['unverified_constraints']))
        return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError, EOFError) as exc:
        print(f'ERROR: {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
