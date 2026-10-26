"""Offline second-recipe review. Preserve unknowns; never invent brewing inputs."""
import argparse
import json
from pathlib import Path

from .myspeidel_put_roundtrip import read_backup, private_file, write_new, digest
from .myspeidel_guided_import import MAP_FORMAT, normal
from .myspeidel_import_builder import KINDS


def review(recipe, registry=None):
    if registry is not None and registry.get('format') != MAP_FORMAT:
        raise ValueError('Unexpected ingredient mapping format')
    issues=[]; mapping=[]
    references=recipe.get('references',{})
    account=recipe.get('owner',{}).get('uuid')
    saved=(registry or {}).get('accounts',{}).get(account,{})
    def issue(code,path,detail):
        issues.append({'code':code,'path':path,'detail':detail})
    for kind in KINDS:
        for uid,obj in references.get(kind,{}).items():
            name=obj.get('name')
            if obj.get('uuid')!=uid:
                issue('reference_identity_mismatch',f'references.{kind}.{uid}','Map key differs from object UUID')
            if not isinstance(name,str) or not name.strip():
                issue('missing_catalog_name',f'references.{kind}.{uid}.name','Resolve identity from source evidence; do not guess')
                mapping.append({'category':kind,'name':name,'uuid':uid,'status':'unresolved_name'})
                continue
            by_name=saved.get(kind,{}).get(normal(name))
            identical=[v for v in saved.get(kind,{}).values() if v.get('uuid')==uid and v.get('name')==name]
            status='new_mapping'
            if identical:status='reusable_identity'
            elif by_name:status='name_match_different_identity'
            if obj.get('deleted',0)!=0:
                status='deleted';issue('deleted_reference',f'references.{kind}.{uid}','Catalog entry marked deleted')
            mapping.append({'category':kind,'name':name,'uuid':uid,'status':status})
    def name(kind,uid,path):
        obj=references.get(kind,{}).get(uid)
        if obj is None:
            issue('missing_reference',path,'Addition has no matching catalog object')
            return None
        return obj.get('name')
    malts=[]
    for i,x in enumerate(recipe['mashing']['adds'].get('malts',[])):
        uid=x['malt_uuid'];label=name('malts',uid,f'mashing.adds.malts[{i}]')
        malts.append({'name':label,'amount_kg':x['amount'],'source_color_ebc':x.get('color')})
        if x.get('color') in (None,0):
            issue('malt_color_unconfirmed',f'mashing.adds.malts[{i}].color','Zero/null retained as source value; verify product specification')
    hops=[]
    for i,step in enumerate(recipe['boil']['steps']):
        for j,x in enumerate(step.get('adds',{}).get('hops',[])):
            uid=x['hop_uuid'];path=f'boil.steps[{i}].adds.hops[{j}]'
            catalog=references.get('hops',{}).get(uid,{})
            hops.append({'name':name('hops',uid,path),'amount_g':x['amount'],
                         'remaining_min':step['duration'],'addition_alpha_percent':x.get('acid'),
                         'catalog_alpha_percent':catalog.get('acid')})
            if catalog.get('acid') is not None and x.get('acid')!=catalog['acid']:
                issue('alpha_conflict',path+'.acid','Addition and catalog alpha differ; retain both until confirmed')
        if step.get('adds',{}).get('ingredients'):
            issue('misc_requires_mapping',f'boil.steps[{i}].adds.ingredients','Review non-hop additions separately before canonical conversion')
    yeast=recipe.get('fermentation',{}).get('adds',{}).get('yeasts',[])
    if not yeast:issue('missing_yeast','fermentation.adds.yeasts','Specify culture and quantity')
    if not recipe.get('fermentation',{}).get('steps'):
        issue('missing_fermentation_schedule','fermentation.steps','Specify desired fermentation temperature/process')
    water=recipe['mashing']['adds']['water']
    water_name=name('water_types',water.get('uuid'),'mashing.adds.water')
    if water_name is None:
        issue('water_assignment_required','mashing.adds.water.uuid','Confirm water profile; RO is not inferred from another recipe')
    if recipe.get('color') in (None,0):
        issue('recipe_color_unconfirmed','color','Source color is zero/null, not a verified calculated color')
    issue('packaged_volume_required','targets.packaged_volume_l','water_recast is wort volume; confirm packaged volume independently')
    issue('packaging_required','packaging','No canonical packaging plan is inferred from this API backup')
    if recipe['boil'].get('boiling_temperature',0)>100:
        issue('boil_temperature_review','boil.boiling_temperature','Retain source setpoint; confirm before converting it into a physical process target')
    return {'format':'homebrew-as-code/myspeidel-recipe-review-v1','offline':True,
            'source_sha256':digest(recipe),'upload_ready':False,
            'canonical_recipe_created':False,'name':recipe['name'],
            'observed':{'style':recipe.get('style'),'wort_volume_l':recipe.get('water_recast'),
                'original_gravity_plato':recipe.get('water_plato'),'specific_gravity':recipe.get('water_specific_gravity'),
                'bitterness_ibu':recipe.get('bitterness'),'source_color_ebc':recipe.get('color'),
                'malts':malts,'mash_in_temperature_c':recipe['mashing']['temperature'],
                'mash_steps':recipe['rest']['steps'],
                'water':{'name':water_name,'mash_l':water['water_amount_start'],'sparge_l':recipe['rest']['water_amount_addition']},
                'boil_duration_min':recipe['boil']['boiling_duration'],
                'boil_temperature_c':recipe['boil']['boiling_temperature'],'hops':hops,
                'yeast_additions':yeast},
            'ingredient_mapping':mapping,'review_items':issues,
            'next_step':'Resolve review items, then author a canonical recipe and independent brew plan. No upload candidate was created.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup',required=True)
    parser.add_argument('--mapping',default='.local/myspeidel-ingredient-mapping.json')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    try:
        destination=private_file(args.output)
        _,source,_=read_backup(private_file(args.backup,must_exist=True))
        mapping_path=Path(args.mapping)
        registry=None
        if mapping_path.exists():
            registry=json.loads(private_file(args.mapping,must_exist=True).read_text(encoding='utf-8-sig'))
        result=review(source,registry)
        write_new(destination,result)
        print('Recipe:',json.dumps(result['name'],ensure_ascii=True))
        for item in result['ingredient_mapping']:
            print(item['category'],json.dumps(item['name'],ensure_ascii=True),'->',item['status'])
        print('Review items:',len(result['review_items']))
        for item in result['review_items']:
            print(' ',item['code']+':',item['path'])
        print('Report:',destination)
        print('Offline review completed. No canonical recipe, upload candidate or API request created.')
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('Review stopped:',type(exc).__name__)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
