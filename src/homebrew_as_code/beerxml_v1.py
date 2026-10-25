"""Independent BeerXML 1.0 exporter from canonical Homebrew-as-Code YAML.

No Brewfather proprietary extensions; no HTTP, vendor identities, or silent assumptions.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from .recipe import load_recipe


class BeerXmlError(ValueError):
    pass


def dec(value, label, *, zero=False):
    if isinstance(value, bool) or value is None:
        raise BeerXmlError(f'Missing numeric: {label}')
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise BeerXmlError(f'Invalid numeric: {label}') from None
    if not x.is_finite() or x < 0 or (x == 0 and not zero):
        raise BeerXmlError(f'Invalid numeric: {label}')
    return x


def fmt(x):
    return format(x, 'f')


def elem(parent, tag, value):
    ET.SubElement(parent, tag).text = str(value)


def record(parent, tag, fields):
    e = ET.SubElement(parent, tag)
    for key, value in fields:
        elem(e, key, value)
    return e


def validate_xml(xml_bytes):
    """Subset of BeerXML 1.0 structural/semantic validation; not an XSD validator."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise BeerXmlError('Invalid XML') from e
    if root.tag != 'RECIPES' or len(root.findall('RECIPE')) != 1:
        raise BeerXmlError('Expected exactly one RECIPES/RECIPE')
    recipe = root.find('RECIPE')
    def required(node, tags):
        for tag in tags:
            x = node.find(tag)
            if x is None or not x.text or not x.text.strip():
                raise BeerXmlError(f'Missing {node.tag}/{tag}')
    required(recipe, ['NAME', 'VERSION', 'TYPE', 'BREWER', 'BATCH_SIZE', 'BOIL_SIZE', 'BOIL_TIME', 'EFFICIENCY'])
    if recipe.findtext('TYPE') != 'All Grain':
        raise BeerXmlError('Only All Grain export is supported')
    style = recipe.find('STYLE')
    if style is None:
        raise BeerXmlError('STYLE is required')
    required(style, ['NAME', 'CATEGORY', 'VERSION', 'CATEGORY_NUMBER', 'STYLE_LETTER', 'STYLE_GUIDE', 'TYPE'])
    for container, child, fields in [
        ('HOPS','HOP',['NAME','VERSION','ALPHA','AMOUNT','USE','TIME']),
        ('FERMENTABLES','FERMENTABLE',['NAME','VERSION','TYPE','AMOUNT','YIELD','COLOR']),
        ('MISCS','MISC',['NAME','VERSION','TYPE','USE','TIME','AMOUNT','AMOUNT_IS_WEIGHT']),
        ('YEASTS','YEAST',['NAME','VERSION','TYPE','FORM','AMOUNT']),
    ]:
        node = recipe.find(container)
        if node is None:
            raise BeerXmlError(f'{container} is required by this profile')
        for sub in node.findall(child):
            required(sub, fields)
    mash = recipe.find('MASH')
    if mash is None or mash.find('MASH_STEPS') is None:
        raise BeerXmlError('All Grain MASH/MASH_STEPS is required by this profile')
    for step in mash.find('MASH_STEPS').findall('MASH_STEP'):
        required(step, ['NAME','VERSION','TYPE','STEP_TEMP','STEP_TIME'])
    # Assert no proprietary extension fields are emitted.
    if any(x.tag.startswith('BF_') for x in root.iter()):
        raise BeerXmlError('Brewfather extensions are not allowed')
    return root


def export(data, *, boil_size_l, efficiency_percent, malt_specs, honey_yield_percent,
           honey_color_lovibond, grain_temp_c=None, title=None):
    """Build standards-oriented XML with explicitly provided missing brew-house values.

    malt_specs is an index-keyed mapping with yield_percent and color_lovibond.
    All malt colors are explicit, not guessed from malt names.
    """
    recipe = data['recipe']; targets = data['targets']; mash = data['mash']; boil = data['boil']
    bsize = dec(targets['packaged_volume_l'], 'targets.packaged_volume_l')
    bsize_boil = dec(boil_size_l, 'boil_size_l')
    if bsize_boil <= bsize:
        raise BeerXmlError('BOIL_SIZE must exceed BATCH_SIZE; do not use total water as boil size')
    eff = dec(efficiency_percent, 'efficiency_percent')
    if eff > 100:
        raise BeerXmlError('EFFICIENCY must not exceed 100%')
    if len(malt_specs) != len(data['fermentables']):
        raise BeerXmlError('Supply verified/declared YIELD and COLOR for every malt index')
    root = ET.Element('RECIPES'); r = ET.SubElement(root, 'RECIPE')
    elem(r, 'NAME', title or recipe['name'])
    elem(r, 'VERSION', '1'); elem(r, 'TYPE', 'All Grain')
    elem(r, 'BREWER', 'Homebrew-as-Code')
    # A user-defined style, not an assertion of an official BJCP classification.
    record(r, 'STYLE', [('NAME',recipe['style']),('CATEGORY','Homebrew-as-Code custom'),
        ('VERSION','1'),('CATEGORY_NUMBER','0'),('STYLE_LETTER','A'),
        ('STYLE_GUIDE','Custom'),('TYPE','Ale')])
    elem(r, 'BATCH_SIZE', fmt(bsize)); elem(r, 'BOIL_SIZE',fmt(bsize_boil))
    elem(r, 'BOIL_TIME',fmt(dec(boil['duration_min'],'boil.duration_min')))
    elem(r, 'EFFICIENCY',fmt(eff))
    elem(r, 'CARBONATION',fmt(dec(targets['carbonation_volumes'],'targets.carbonation_volumes')))
    # Numeric original gravity target is not asserted as a measured OG.
    notes = [
        'Canonical Homebrew-as-Code YAML; target original gravity '
        f"{targets['original_gravity_plato']} Plato; target ABV {targets['alcohol_abv_percent']}%; "
        f"target bitterness {targets['bitterness_ibu']} IBU.",
        f"Mash-in water temperature {mash['mash_in_temperature_c']} C (NOT grain temperature).",
        f"Water {data['water']['mash_l']} L mash + {data['water']['sparge_l']} L sparge; total water "
        f"{data['water']['total_l']} L is NOT BOIL_SIZE.",
        f"Water salts (g): {data['water']['salts_g']}; RO residual ions unverified.",
        'Honey is listed as FERMENTABLE (sugar); timing in boil additions is 10 minutes remaining.',
        f"Spice contact after flameout: {boil.get('spice_contact_after_flameout_min', 0)} min.",
        f"Target fermentation temperature: {data['yeast']['fermentation_temperature_c']} C.",
        'All ingredients and targets require review in MySpeidel before saving.',
    ]
    elem(r, 'NOTES',' '.join(notes))
    hops = ET.SubElement(r,'HOPS'); ferm = ET.SubElement(r,'FERMENTABLES')
    misc = ET.SubElement(r,'MISCS'); yeast = ET.SubElement(r,'YEASTS')
    warnings = ['Custom STYLE fields are self-declared, not an official BJCP style.',
                'Efficiency, BOIL_SIZE, malt yields/colors and honey properties were explicitly supplied at export time.',
                'OG/FG, measured gravity, fermentation duration, equipment losses and mineral-water profiles were not invented.',
                'Ingredient identity and compatibility with MySpeidel require interactive review.',
                'Mash-in water temperature is retained in NOTES, not incorrectly written to GRAIN_TEMP.',
                'Water and salt quantities are retained in NOTES; not losslessly represented in BeerXML 1.0.']
    for i, malt in enumerate(data['fermentables']):
        spec = malt_specs.get(str(i))
        if not isinstance(spec, dict):
            raise BeerXmlError(f'Missing malt properties for index {i}')
        yield_pct = dec(spec.get('yield_percent'), f'malt[{i}].yield_percent')
        color = dec(spec.get('color_lovibond'),f'malt[{i}].color_lovibond',zero=True)
        if yield_pct > 100:
            raise BeerXmlError(f'Yield >100 at index {i}')
        record(ferm,'FERMENTABLE',[('NAME',malt['name']),('VERSION',1),('TYPE','Grain'),
            ('AMOUNT',fmt(dec(malt['amount_g'],f'malt[{i}].amount_g')/1000)),
            ('YIELD',fmt(yield_pct)),('COLOR',fmt(color))])
    honey = [a for a in boil['additions'] if a['ingredient'].lower() == 'mild honey']
    if len(honey) != 1:
        raise BeerXmlError('Expected one Mild honey boil addition')
    if dec(honey_yield_percent,'honey_yield_percent') > 100:
        raise BeerXmlError('Honey yield must not exceed 100%')
    record(ferm,'FERMENTABLE',[('NAME',honey[0]['ingredient']),('VERSION',1),('TYPE','Sugar'),
        ('AMOUNT',fmt(dec(honey[0]['amount_g'],'honey.amount_g')/1000)),
        ('YIELD',fmt(dec(honey_yield_percent,'honey_yield_percent'))),
        ('COLOR',fmt(dec(honey_color_lovibond,'honey_color_lovibond',zero=True))),
        ('ADD_AFTER_BOIL','FALSE')])
    for item in boil['additions']:
        name = item['ingredient']; minute = fmt(dec(item['remaining_min'],f'{name}.remaining_min',zero=True))
        amt = fmt(dec(item['amount_g'],f'{name}.amount_g')/1000)
        if 'alpha_acid_percent' in item:
            record(hops,'HOP',[('NAME',name),('VERSION',1),
                ('ALPHA',fmt(dec(item['alpha_acid_percent'],f'{name}.alpha'))),
                ('AMOUNT',amt),('USE','Boil'),('TIME',minute),('FORM','Pellet')])
        elif item is not honey[0]:
            if name not in {'Ceylon cinnamon sticks', 'Fresh ginger', 'Whole cloves', 'Nutmeg', 'Orange zest'}:
                raise BeerXmlError(f'Unclassified boil addition: {name}; do not silently map to Spice')
            record(misc,'MISC',[('NAME',name),('VERSION',1),('TYPE','Spice'),('USE','Boil'),
                ('TIME',minute),('AMOUNT',amt),('AMOUNT_IS_WEIGHT','TRUE')])
    y = data['yeast']
    record(yeast,'YEAST',[('NAME',y['name']),('VERSION',1),('TYPE','Ale'),('FORM','Dry'),
        ('AMOUNT',fmt(dec(y['amount_g'],'yeast.amount_g')/1000)),('AMOUNT_IS_WEIGHT','TRUE'),
        ('LABORATORY','Fermentis'),('PRODUCT_ID','S-04')])
    m = ET.SubElement(r,'MASH'); elem(m,'NAME','Homebrew-as-Code temperature mash')
    elem(m,'VERSION','1')
    if grain_temp_c is not None:
        elem(m,'GRAIN_TEMP',fmt(dec(grain_temp_c,'grain_temp_c',zero=True)))
    steps = ET.SubElement(m,'MASH_STEPS')
    for i, step in enumerate(mash['steps']):
        record(steps,'MASH_STEP',[('NAME',f'Rest {i+1}'),('VERSION',1),('TYPE','Temperature'),
            ('STEP_TEMP',fmt(dec(step['temperature_c'],f'mash.step[{i}].temp'))),
            ('STEP_TIME',fmt(dec(step['duration_min'],f'mash.step[{i}].minutes')))])
    ET.indent(root, space='  ')
    xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    validate_xml(xml)
    return xml, {'format':'homebrew-as-code/beerxml-v1-export', 'status':'STRUCTURALLY_VALIDATED_NOT_IMPORT_VERIFIED',
                 'recipe':recipe['name'],'sha256':hashlib.sha256(xml).hexdigest(),
                 'malt_count':len(data['fermentables']),'hop_count':len(hops),'misc_count':len(misc),
                 'yeast_count':len(yeast),'mash_step_count':len(steps), 'warnings':warnings,
                 'unsupported_fields':['mash_in_water_temperature_as_structured_step','mash_and_sparge_water',
                                      'water_salts','fermentation_temperature_range','packaged_volume_vs_batch_size',
                                      'spice_contact_after_flameout']}


def main(argv=None):
    p = argparse.ArgumentParser(description='Independent BeerXML 1.0 exporter (offline)')
    p.add_argument('--recipe',required=True)
    p.add_argument('--xml',required=True)
    p.add_argument('--report',required=True)
    p.add_argument('--boil-size-liters',required=True)
    p.add_argument('--efficiency-percent',required=True)
    p.add_argument('--properties-json',required=True,help='Local JSON with malt_specs, honey_yield_percent, honey_color_lovibond')
    p.add_argument('--grain-temp-c')
    p.add_argument('--name')
    args = p.parse_args(argv)
    try:
        values = json.loads(Path(args.properties_json).read_text(encoding='utf-8'))
        xml, report = export(load_recipe(args.recipe),boil_size_l=args.boil_size_liters,
            efficiency_percent=args.efficiency_percent,malt_specs=values['malt_specs'],
            honey_yield_percent=values['honey_yield_percent'],
            honey_color_lovibond=values['honey_color_lovibond'],
            grain_temp_c=args.grain_temp_c,title=args.name)
        out=Path(args.xml); rep=Path(args.report)
        if out.exists() or rep.exists():
            raise BeerXmlError('Output exists; refusing overwrite')
        out.parent.mkdir(parents=True,exist_ok=True);rep.parent.mkdir(parents=True,exist_ok=True)
        with out.open('xb') as handle: handle.write(xml)
        with rep.open('x',encoding='utf-8') as handle: json.dump(report,handle,indent=2)
        print('BeerXML written; standard subset validated; MySpeidel import NOT verified.')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'BeerXML export failed: {type(exc).__name__}: {str(exc)[:180]}',file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
