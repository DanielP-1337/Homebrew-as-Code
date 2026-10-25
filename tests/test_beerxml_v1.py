import copy
import xml.etree.ElementTree as ET
import pytest
from homebrew_as_code.beerxml_v1 import BeerXmlError, export, validate_xml

RECIPE = {
 'recipe':{'name':'Lebkuchen-Zauber 2026','style':'Christmas Brown Ale'},
 'targets':{'packaged_volume_l':20,'original_gravity_plato':14,'alcohol_abv_percent':5.7,
            'bitterness_ibu':21,'carbonation_volumes':2.2},
 'mash':{'mash_in_temperature_c':60,'steps':[{'temperature_c':63,'duration_min':20},
         {'temperature_c':72,'duration_min':45},{'temperature_c':78,'duration_min':10}]},
 'boil':{'duration_min':60,'spice_contact_after_flameout_min':5,'additions':[
  {'remaining_min':60,'ingredient':'Goldings pellets','amount_g':60,'alpha_acid_percent':2.9},
  {'remaining_min':10,'ingredient':'Mild honey','amount_g':250},
  *[{'remaining_min':5,'ingredient':name,'amount_g':grams} for name,grams in
    [('Ceylon cinnamon sticks',5),('Fresh ginger',12),('Whole cloves',.2),('Nutmeg',.3),('Orange zest',8)]]]},
 'fermentables':[{'name':n,'amount_g':g} for n,g in
   [('Pale Ale Malt',2800),('Munich Malt Type II',1500),('CaraMunich II',450),
    ('Melanoidin Malt',250),('Chocolate Malt',100)]],
 'yeast':{'name':'Fermentis SafAle S-04','amount_g':11.5,'fermentation_temperature_c':[18,20]},
 'water':{'mash_l':23,'sparge_l':5,'total_l':28,'salts_g':{'calcium_chloride_dihydrate':5,'calcium_sulfate_dihydrate':3}}
}
SPECS={str(i):{'yield_percent':75,'color_lovibond':n} for i,n in enumerate([2,9,45,15,350])}
def run(**kwargs):
  return export(copy.deepcopy(RECIPE),boil_size_l=25,efficiency_percent=70,malt_specs=SPECS,
                honey_yield_percent=80,honey_color_lovibond=1,**kwargs)

def test_export_quantities_and_sections():
  xml, report=run()
  root=validate_xml(xml);r=root.find('RECIPE')
  assert r.findtext('EFFICIENCY')=='70'
  assert r.findtext('BOIL_SIZE')=='25'
  assert len(r.findall('./FERMENTABLES/FERMENTABLE'))==6
  assert r.findtext('./FERMENTABLES/FERMENTABLE/AMOUNT')=='2.8'
  assert r.findall('./FERMENTABLES/FERMENTABLE')[-1].findtext('AMOUNT')=='0.25'
  assert r.findtext('./HOPS/HOP/AMOUNT')=='0.06'
  assert r.findtext('./YEASTS/YEAST/AMOUNT')=='0.0115'
  assert len(r.findall('./MISCS/MISC'))==5
  assert len(r.findall('./MASH/MASH_STEPS/MASH_STEP'))==3
  assert r.find('./MASH/GRAIN_TEMP') is None
  assert 'BF_ID' not in xml.decode()
  assert report['status']=='STRUCTURALLY_VALIDATED_NOT_IMPORT_VERIFIED'

def test_missing_malt_properties_fail_closed():
  with pytest.raises(BeerXmlError):
    export(RECIPE,boil_size_l=25,efficiency_percent=70,malt_specs={},honey_yield_percent=80,honey_color_lovibond=1)

@pytest.mark.parametrize('boil', [20, 19, 'NaN', '-1'])
def test_bad_boil_size(boil):
  with pytest.raises(BeerXmlError):
    export(RECIPE,boil_size_l=boil,efficiency_percent=70,malt_specs=SPECS,honey_yield_percent=80,honey_color_lovibond=1)

def test_grain_temperature_not_mash_in():
  xml,_=run(grain_temp_c=19)
  assert ET.fromstring(xml).findtext('./RECIPE/MASH/GRAIN_TEMP')=='19'

def test_required_style_validation():
  xml,_=run();root=ET.fromstring(xml);root.find('RECIPE').remove(root.find('./RECIPE/STYLE'))
  with pytest.raises(BeerXmlError):validate_xml(ET.tostring(root))

def test_unknown_ingredient_not_silently_misclassified():
  d=copy.deepcopy(RECIPE)
  d['boil']['additions'].append({'remaining_min':5,'ingredient':'Extra Spice','amount_g':3})
  with pytest.raises(BeerXmlError, match='Unclassified boil addition'):
    export(d,boil_size_l=25,efficiency_percent=70,malt_specs=SPECS,honey_yield_percent=80,honey_color_lovibond=1)
