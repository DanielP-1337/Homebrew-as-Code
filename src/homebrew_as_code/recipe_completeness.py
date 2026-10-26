"""Versioned draft recipes: unknown quantities are not zero or fabricated targets."""
import argparse
import json
import math
from pathlib import Path
import yaml
from .recipe import RecipeError


def number(value, name, *, zero=False):
    if type(value) not in (int,float) or not math.isfinite(value) or value < 0 or (not zero and value == 0):
        raise RecipeError(name + ' must be finite and ' + ('nonnegative' if zero else 'positive'))


def validate_draft(data):
    if not isinstance(data,dict) or data.get('schema_version')!=2:
        raise RecipeError('Expected draft recipe schema_version 2')
    for key in ('id','name','version','style'):
        if not isinstance(data.get('recipe',{}).get(key),str) or not data['recipe'][key].strip():
            raise RecipeError('Missing recipe.'+key)
    if data['recipe'].get('status')!='draft':
        raise RecipeError('Schema 2 currently supports draft status only')
    targets=data.get('targets')
    if not isinstance(targets,dict):raise RecipeError('Missing targets')
    for key in ('packaged_volume_l','original_gravity_plato','alcohol_abv_percent','bitterness_ibu'):
        if targets.get(key) is not None:number(targets[key],key)
    control=data.get('gravity_control',{})
    if control.get('mode')!='target_gravity_variable_yield' or control.get('measurement_stage')!='after_mash':
        raise RecipeError('Expected explicit after-mash gravity control with variable yield')
    number(control.get('target_plato'),'gravity target')
    if targets.get('packaged_volume_l') is not None:
        raise RecipeError('Variable-yield draft must not impose packaged volume')
    mash=data.get('mash',{});number(mash.get('mash_in_temperature_c'),'mash in')
    steps=mash.get('steps')
    if not isinstance(steps,list) or not 1<=len(steps)<=10:raise RecipeError('Expected 1-10 mash steps')
    for row in steps:
        number(row.get('temperature_c'),'mash temperature');number(row.get('duration_min'),'mash duration')
        if row['temperature_c']>100:raise RecipeError('Mash temperature exceeds 100 C')
    grains=data.get('fermentables')
    if not isinstance(grains,list) or not grains:raise RecipeError('Missing fermentables')
    for row in grains:
        if not row.get('name') or row.get('purchase_form')!='whole':raise RecipeError('Whole named malt required')
        number(row.get('amount_g'),'malt amount')
    boil=data.get('boil',{});number(boil.get('duration_min'),'boil duration')
    if boil.get('temperature_c') is not None:number(boil['temperature_c'],'boil temperature')
    for row in boil.get('additions',[]):
        if not row.get('ingredient'):raise RecipeError('Missing addition name')
        number(row.get('amount_g'),'addition amount');number(row.get('remaining_min'),'addition time',zero=True)
        if row['remaining_min']>boil['duration_min']:raise RecipeError('Addition before boil')
        if row.get('alpha_acid_percent') is not None:
            number(row['alpha_acid_percent'],'alpha')
            if row['alpha_acid_percent']>100:raise RecipeError('Alpha exceeds 100 percent')
    water=data.get('water',{})
    for key in ('total_l','mash_l','sparge_l'):number(water.get(key),key,zero=key=='sparge_l')
    if abs(water['total_l']-water['mash_l']-water['sparge_l'])>1e-6:raise RecipeError('Water sum mismatch')
    if not water.get('source'):raise RecipeError('Water source required')
    yeast=data.get('yeast',{})
    if not yeast.get('name'):raise RecipeError('Yeast required')
    number(yeast.get('amount_g'),'yeast amount')
    ambient=data.get('fermentation',{}).get('ambient_temperature_c')
    if ambient is not None:number(ambient,'ambient temperature')


def load_draft(path):
    try:data=yaml.safe_load(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError,yaml.YAMLError) as exc:raise RecipeError('Cannot read draft recipe') from exc
    validate_draft(data)
    return data


def assess(data, settings=None):
    validate_draft(data)
    settings=settings or {}
    from .myspeidel_export_profile import export_recipe
    data, _, _, _ = export_recipe(data, settings)
    blockers=[]
    if data['boil'].get('temperature_c') is None:blockers.append('boil.temperature_c: confirm export temperature; historical controller setpoint is separate')
    if data['targets'].get('original_gravity_plato') is None:blockers.append('targets.original_gravity_plato: confirm final OG separately from after-mash measurement')
    if settings.get('wort_volume_l') is None:blockers.append('settings.wort_volume_l: supply explicit batch/export wort volume; equipment size is not yield')
    else:number(settings['wort_volume_l'],'export wort volume')
    for grain in data['fermentables']:
        value=settings.get('malt_colors_ebc',{}).get(grain['name'])
        if value is None:blockers.append('malt color: '+grain['name'])
        else:number(value,'malt color',zero=True)
    return {'format':'homebrew-as-code/draft-completeness-v1','domain_valid':True,
            'brew_plan_linkable':True,'upload_ready':False,
            'quantity_mode':'target_gravity_variable_yield',
            'gravity_control':data['gravity_control'],
            'optional_unknowns':[key for key in ('packaged_volume_l','alcohol_abv_percent','bitterness_ibu') if data['targets'].get(key) is None],
            'myspeidel_mapping_blockers':blockers,
            'later_checks':['Catalog identities and metadata','Account/equipment policy','POST schema and dry-run'],
            'note':'Passing this report does not assert measured yield, final OG, calculated IBU or API acceptance.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--recipe',default='recipes/weizen-nikolaus/recipe.yaml')
    p.add_argument('--settings')
    args=p.parse_args(argv)
    try:
        settings=json.loads(Path(args.settings).read_text(encoding='utf-8-sig')) if args.settings else None
        report=assess(load_draft(args.recipe),settings)
        print(json.dumps(report,indent=2,ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('Completeness check failed:',str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
