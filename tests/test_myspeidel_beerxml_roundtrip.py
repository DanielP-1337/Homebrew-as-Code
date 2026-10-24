"""No-network BeerXML Golden Roundtrip tests."""
import xml.etree.ElementTree as ET
from decimal import Decimal
import pytest
from homebrew_as_code.myspeidel_beerxml_roundtrip import export, compare


def recipe(uid='A'):
    return {
        'name': 'Weizenbier 38', 'uuid': uid,
        'mashing': {'adds': {'malts': [{'malt_uuid': 'm1', 'amount': 2}]}},
        'boil': {'boiling_duration': 80, 'steps': [
            {'duration': 70, 'adds': {'hops': [{'hop_uuid': 'h1', 'amount': 15, 'acid': 4.2}]}}]},
        'references': {'malts': {'m1': {'name': 'Weizen Malz', 'color': 4}},
                       'hops': {'h1': {'name': 'Tettnanger', 'acid': 4.2}}},
    }


def test_beerxml_core_and_no_cloud_uuid():
    xml, report = export(recipe(), 'HBAC Test', batch_size=20, boil_size=23,
                         assumed_yield=75)
    node = ET.fromstring(xml)
    assert node.findtext('RECIPE/NAME') == 'HBAC Test'
    assert node.findtext('RECIPE/BATCH_SIZE') == '20'
    assert node.findtext('RECIPE/FERMENTABLES/FERMENTABLE/YIELD') == '75'
    assert node.findtext('RECIPE/HOPS/HOP/AMOUNT') == '0.015'
    assert node.findtext('RECIPE/HOPS/HOP/TIME') == '70'
    assert b'm1' not in xml and b'h1' not in xml
    assert report['status'] == 'PARTIAL_EXPORT'


def test_missing_hop_time_refuses_guess():
    r = recipe()
    del r['boil']['steps'][0]['duration']
    with pytest.raises(ValueError, match='Missing boil step time'):
        export(r, 'HBAC', batch_size=20, boil_size=23, assumed_yield=75)


def test_missing_malt_name_refuses_guess():
    r = recipe()
    r['references']['malts']['m1']['name'] = None
    with pytest.raises(ValueError, match='Missing malt name'):
        export(r, 'HBAC', batch_size=20, boil_size=23, assumed_yield=75)


def test_compare_ignores_uuids_but_checks_semantics():
    a = recipe('A')
    b = recipe('B')
    b['mashing']['adds']['malts'][0]['malt_uuid'] = 'new-m'
    b['boil']['steps'][0]['adds']['hops'][0]['hop_uuid'] = 'new-h'
    b['references']['malts']['new-m'] = b['references']['malts'].pop('m1')
    b['references']['hops']['new-h'] = b['references']['hops'].pop('h1')
    assert compare(a, b)['status'] == 'EQUIVALENT_FOR_CHECKED_FIELDS'
    b['boil']['steps'][0]['adds']['hops'][0]['amount'] = 12
    assert compare(a, b)['status'] == 'DIFFERENCES_FOUND'


def test_invalid_nonnumeric_or_negative_malt():
    r = recipe()
    r['mashing']['adds']['malts'][0]['amount'] = '-1'
    with pytest.raises(ValueError):
        export(r, 'HBAC', batch_size=20, boil_size=23, assumed_yield=75)


def test_explicit_missing_color_override_audited():
    r = recipe()
    r['references']['malts']['m1']['color'] = None
    with pytest.raises(ValueError, match='color_EBC'):
        export(r, 'HBAC', batch_size=20, boil_size=23, assumed_yield=75)
    xml, report = export(r, 'HBAC', batch_size=20, boil_size=23,
                         assumed_yield=75, malt_color_overrides={0: '24'})
    assert report['malt_color_overrides'] == [
        {'malt_index': 0, 'name': 'Weizen Malz', 'color_ebc': '24',
         'source': 'manual_web_form_evidence'}]
    assert Decimal(ET.fromstring(xml).findtext('RECIPE/FERMENTABLES/FERMENTABLE/COLOR')) == Decimal('24') / Decimal('1.97')


def test_override_rejects_existing_cloud_color_and_bad_index():
    with pytest.raises(ValueError, match='cloud value exists'):
        export(recipe(), 'HBAC', batch_size=20, boil_size=23, assumed_yield=75,
               malt_color_overrides={0: 24})
    with pytest.raises(ValueError, match='Invalid malt color overrides'):
        export(recipe(), 'HBAC', batch_size=20, boil_size=23, assumed_yield=75,
               malt_color_overrides={4: 24})


def test_observed_mash_schedule_is_emitted_without_water_guess():
    xml, report = export(recipe(), 'HBAC', batch_size=20, boil_size=23,
                         assumed_yield=75, mash_in_temp='38',
                         mash_steps=[('62', '30'), ('72', '40'), ('78', '10')])
    node = ET.fromstring(xml)
    assert [x.text for x in node.findall('RECIPE/MASH/MASH_STEPS/MASH_STEP/STEP_TEMP')] == ['62', '72', '78']
    assert [x.text for x in node.findall('RECIPE/MASH/MASH_STEPS/MASH_STEP/STEP_TIME')] == ['30', '40', '10']
    assert node.find('RECIPE/MASH/MASH_STEPS/MASH_STEP/INFUSE_AMOUNT') is None
    assert len(report['mash_steps']) == 3


def test_incomplete_mash_evidence_fails_closed():
    with pytest.raises(ValueError, match='both mash-in'):
        export(recipe(), 'HBAC', batch_size=20, boil_size=23,
               assumed_yield=75, mash_steps=[('62', '30')])


def test_explicit_yeast_metadata_does_not_guess_amount():
    r = recipe()
    r['fermentation'] = {'adds': {'yeasts': [{'yeast_uuid': 'y1', 'amount': 15}]}}
    r['references']['yeasts'] = {'y1': {'name': 'Weizen Hefe'}}
    xml, report = export(r, 'HBAC', batch_size=20, boil_size=23, assumed_yield=75,
                         yeast_type='Wheat', yeast_form='Dry', yeast_amount_kg='0.015')
    root = ET.fromstring(xml)
    assert root.findtext('RECIPE/YEASTS/YEAST/NAME') == 'Weizen Hefe'
    assert root.findtext('RECIPE/YEASTS/YEAST/AMOUNT') == '0.015'
    assert report['yeast_count'] == 1
    xml2, report2 = export(r, 'HBAC', batch_size=20, boil_size=23, assumed_yield=75)
    assert ET.fromstring(xml2).find('RECIPE/YEASTS') is None
    assert report2['yeast_count'] == 0
