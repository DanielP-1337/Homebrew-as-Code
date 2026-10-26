"""Offline MySpeidel import drafts. No credentials, transport or identity invention."""
from __future__ import annotations

from copy import deepcopy
import math
from uuid import UUID

from .recipe import validate_recipe
from .myspeidel_put_roundtrip import digest
from .myspeidel_golden_validation import _issues

TEMPLATE_FORMAT = 'homebrew-as-code/myspeidel-import-template-v1'
KINDS = ('water_types', 'malts', 'hops', 'ingredients', 'yeasts')


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected non-empty text')
    return value


def _number(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{label}: expected finite non-negative number')
    return value


def _uuid(value):
    if not isinstance(value, str) or str(UUID(value)) != value.lower():
        raise ValueError('Invalid reference UUID')
    return value


def make_template(recipe):
    """Extract reference identities only; never inherit recipe data or ownership.

    Catalog UUIDs are account-specific evidence, not globally portable IDs.
    All required API metadata must be resolved separately before a future POST.
    """
    refs = {kind: [] for kind in KINDS}
    for kind in KINDS:
        for key, obj in recipe.get('references', {}).get(kind, {}).items():
            if key != obj.get('uuid'):
                raise ValueError('Reference map key/UUID mismatch')
            refs[kind].append({'uuid': _uuid(key), 'name': _text(obj.get('name'))})
        refs[kind].sort(key=lambda x: (x['name'], x['uuid']))
    return {'format': TEMPLATE_FORMAT, 'references': refs}


def _resolve(template, kind, name):
    wanted = ' '.join(_text(name).casefold().split())
    matches = [x for x in template['references'].get(kind, [])
               if ' '.join(_text(x.get('name')).casefold().split()) == wanted]
    if len(matches) != 1:
        raise ValueError(f'{kind}: {name}: expected one exact name match, found {len(matches)}')
    obj = matches[0]
    return {'uuid': _uuid(obj.get('uuid')), 'name': obj['name']}


def inspect_create_contract(spec, candidate):
    """Audit the supplied local contract; schema acceptance is not live evidence."""
    op = spec.get('paths', {}).get('/v1.0/recipe', {}).get('post')
    if not isinstance(op, dict):
        raise ValueError('POST /v1.0/recipe is not documented in supplied spec')
    schema = op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema')
    if not isinstance(schema, dict):
        raise ValueError('POST JSON schema missing')
    errors, unverified = _issues(spec, schema, candidate, '$')
    params = []
    for item in op.get('parameters', []):
        if '$ref' in item:
            from .myspeidel_openapi_reference import _pointer
            item = _pointer(spec, item['$ref'])
        params.append(item)
    return {'method': 'POST', 'path': '/v1.0/recipe',
            'dry_run_documented': any(x.get('name') == 'dryRun' and x.get('in') == 'query' for x in params),
            'spec_sha256': digest(spec), 'schema_errors': errors,
            'unverified_constraints': unverified, 'live_create_verified': False}


def build_import_draft(recipe, template, settings, *, spec=None):
    """Map canonical values with explicit exchange decisions; return draft/report.

    settings: water_name, wort_volume_l (NOT packaged volume), malt_colors_ebc,
    timing_by_ingredient (explicit remaining minutes for every non-hop addition).
    No source recipe values or source addition identities are reused.
    """
    if recipe.get('schema_version') == 2:
        from .recipe_completeness import assess
        status = assess(recipe, settings)
        if status['myspeidel_mapping_blockers']:
            raise ValueError('MySpeidel draft mapping needs: ' + '; '.join(status['myspeidel_mapping_blockers']))
    else:
        validate_recipe(recipe)
    from .myspeidel_export_profile import export_recipe
    recipe, fermentation_steps, maturation_steps, export_profile = export_recipe(recipe, settings)
    if template.get('format') != TEMPLATE_FORMAT:
        raise ValueError('Unexpected template format')
    refs = {kind: {} for kind in KINDS}

    def resolve(kind, name):
        obj = _resolve(template, kind, name)
        refs[kind][obj['uuid']] = obj
        return obj['uuid']

    water_id = resolve('water_types', settings.get('water_name'))
    colors = settings.get('malt_colors_ebc', {})
    malts = []
    for malt in recipe['fermentables']:
        name = malt['name']
        malts.append({'malt_uuid': resolve('malts', name),
                      'amount': _number(malt['amount_g'], name) / 1000,
                      'color': _number(colors.get(name), f'{name} color')})
    duration = _number(recipe['boil']['duration_min'], 'boil duration')
    timings = settings.get('timing_by_ingredient', {})
    expected = {x['ingredient'] for x in recipe['boil']['additions'] if 'alpha_acid_percent' not in x}
    if set(timings) != expected:
        raise ValueError('timing_by_ingredient must cover exactly all non-hop ingredient names')
    grouped = {}
    timing_decisions = []
    for add in recipe['boil']['additions']:
        name = add['ingredient']
        hop = 'alpha_acid_percent' in add
        remaining = _number(add['remaining_min'] if hop else timings[name], f'{name} timing')
        if remaining > duration:
            raise ValueError(f'{name}: addition is before boil start')
        kind, key = ('hops', 'hop_uuid') if hop else ('ingredients', 'ingredient_uuid')
        row = {key: resolve(kind, name), 'amount': _number(add['amount_g'], name),
               'acid': _number(add['alpha_acid_percent'], name) if hop else 0}
        grouped.setdefault(remaining, {}).setdefault(kind, []).append(row)
        if not hop:
            timing_decisions.append({'name': name, 'source_remaining_min': add['remaining_min'],
                                     'mapped_remaining_min': remaining})
    steps = []
    for index, remaining in enumerate(sorted(grouped, reverse=True), 1):
        adds = grouped[remaining]
        for rows in adds.values():
            for row in rows:
                row['hopping_step_number'] = index
        steps.append({'duration': remaining, 'adds': adds})
    yeast = recipe['yeast']
    mash_steps = [{'duration': _number(x['duration_min'], 'mash duration'),
                   'temperature': _number(x['temperature_c'], 'mash temperature')}
                  for x in recipe['mash']['steps']]
    if len(mash_steps) > 10:
        raise ValueError('MySpeidel supports at most 10 mash rests')
    draft = {
        'name': _text(settings.get('export_name', recipe['recipe']['name'])), 'style': recipe['recipe']['style'],
        'public': 0, 'recipe_type': 0,
        'water_plato': _number(recipe['targets']['original_gravity_plato'], 'Plato'),
        'water_recast': _number(settings.get('wort_volume_l'), 'wort volume'),
        'mashing': {'temperature': _number(recipe['mash']['mash_in_temperature_c'], 'mash-in'),
                    'adds': {'water': {'uuid': water_id, 'water_amount_start': _number(recipe['water']['mash_l'], 'mash water')}, 'malts': malts}},
        'rest': {'water_amount_addition': _number(recipe['water']['sparge_l'], 'sparge'), 'steps': mash_steps},
        'boil': {'boiling_duration': duration, 'boiling_temperature': _number(recipe['boil']['temperature_c'], 'boil temperature'), 'steps': steps},
        'fermentation': {'steps': fermentation_steps, 'adds': {'yeasts': [{'yeast_uuid': resolve('yeasts', yeast['name']), 'amount': _number(yeast['amount_g'], 'yeast') }]}},
        'maturation': {'steps': maturation_steps}, 'references': refs,
        'phases': {'1': 'mashing', '2': 'rest', '3': 'boil', '4': 'fermentation', '5': 'maturation'},
    }
    report = {
        'format': 'homebrew-as-code/myspeidel-import-report-v1', 'offline': True,
        'upload_ready': False, 'candidate_sha256': digest(draft),
        'timing_decisions': timing_decisions,
        'export_profile': export_profile,
        'process_units': {'fermentation_duration': 'hours', 'maturation_duration': 'days', 'maturation_pressure': 'bar'} if export_profile else None,
        'unmapped': {'target_bitterness_ibu': recipe['targets'].get('bitterness_ibu'),
                     'fermentation_temperature_c': deepcopy(yeast.get('fermentation_temperature_c')),
                     'fermentation_context': deepcopy(recipe.get('fermentation')),
                     'gravity_control': deepcopy(recipe.get('gravity_control')),
                     'spice_contact_after_flameout_min': recipe['boil'].get('spice_contact_after_flameout_min'),
                     'water_chemistry': deepcopy(recipe['water']), 'packaging': deepcopy(recipe['packaging']),
                     'target_alcohol_abv_percent': recipe['targets'].get('alcohol_abv_percent')},
        'blockers': ['Creation identity and metadata policy is unverified: recipe/addition UUIDs, owner, brewer, dates and versions are intentionally absent.',
                     'Reference metadata is intentionally absent; confirm identities and complete the POST contract before sending.',
                     'Machine reference, color, specific gravity and other required POST fields need explicit mapping.',
                     'Review explicit process settings, unmapped water chemistry and packaging; no schedule is inferred from ambient temperature.',
                     'Target IBU is not a measured or vendor-calculated IBU. No automatic substitution.',
                     'This draft cannot be passed to the existing backup-based PUT/POST commands.'],
    }
    report['create_contract'] = inspect_create_contract(spec, draft) if spec is not None else None
    return draft, report
