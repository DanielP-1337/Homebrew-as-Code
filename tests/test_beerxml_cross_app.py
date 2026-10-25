"""Public synthetic fixtures only; no redistributed Brewfather samples."""
import xml.etree.ElementTree as ET

import pytest

from homebrew_as_code.beerxml_cross_app import compare_xml, _read, RoundtripError


def xml(yeast_amount='0.0115', weight='TRUE', other=False):
    return ET.fromstring(f'''<RECIPE><BATCH_SIZE>20</BATCH_SIZE><BOIL_SIZE>24</BOIL_SIZE>
      <BOIL_TIME>60</BOIL_TIME><EFFICIENCY>70</EFFICIENCY><CARBONATION>2.2</CARBONATION>
      <HOPS><HOP><NAME>Test Hop</NAME><ALPHA>3</ALPHA><AMOUNT>0.06</AMOUNT>
      <USE>Boil</USE><TIME>60</TIME></HOP></HOPS>
      <FERMENTABLES><FERMENTABLE><NAME>Test Malt</NAME><TYPE>Grain</TYPE>
      <AMOUNT>2</AMOUNT><YIELD>80</YIELD><COLOR>3</COLOR></FERMENTABLE></FERMENTABLES>
      <MISCS><MISC><NAME>Test Spice</NAME><TYPE>Spice</TYPE><USE>Boil</USE>
      <TIME>5</TIME><AMOUNT>0.005</AMOUNT><AMOUNT_IS_WEIGHT>TRUE</AMOUNT_IS_WEIGHT></MISC></MISCS>
      <YEASTS><YEAST><NAME>Test Yeast</NAME><AMOUNT>{yeast_amount}</AMOUNT>
      {'' if weight is None else f'<AMOUNT_IS_WEIGHT>{weight}</AMOUNT_IS_WEIGHT>'}</YEAST></YEASTS>
      <MASH><MASH_STEPS><MASH_STEP><STEP_TEMP>63</STEP_TEMP><STEP_TIME>{'25' if other else '20'}</STEP_TIME>
      </MASH_STEP></MASH_STEPS></MASH></RECIPE>''')


def test_equivalence_for_supported_fields():
    result = compare_xml(xml(), xml())
    assert result['status'] == 'SEMANTIC_DIFFERENCES_OR_GAPS'
    assert result['fields']['yeast']['status'] == 'MATCH'


def test_numeric_representation_and_multiset():
    base = xml()
    alt = xml()
    alt.find('./HOPS/HOP/AMOUNT').text = '0.0600'
    assert compare_xml(base, alt)['fields']['hops']['status'] == 'MATCH'


def test_mash_difference_flagged():
    result = compare_xml(xml(), xml(other=True))
    assert result['fields']['mash_steps']['status'] == 'DIFFERENT'


def test_missing_weight_flag_never_misinterpreted():
    result = compare_xml(xml(), xml(yeast_amount='11.5', weight=None))
    assert result['fields']['yeast']['status'] == 'UNIT_SEMANTICS_UNVERIFIED'
    assert result['status'] == 'SEMANTIC_DIFFERENCES_OR_GAPS'


def test_calculated_added_fermentation_not_observed():
    result = compare_xml(xml(), xml())
    assert result['fields']['primary_age']['status'] == 'NOT_OBSERVED'


def test_xml_dtd_rejected(tmp_path):
    f = tmp_path / 'x.xml'
    f.write_text('<!DOCTYPE x [<!ENTITY x "hi">]><RECIPES><RECIPE/></RECIPES>')
    with pytest.raises(RoundtripError, match='DTD'):
        _read(f)


def test_multiple_recipe_rejected(tmp_path):
    f = tmp_path / 'x.xml'
    f.write_text('<RECIPES><RECIPE/><RECIPE/></RECIPES>')
    with pytest.raises(RoundtripError, match='exactly one'):
        _read(f)


def test_cli_requires_private_report(tmp_path):
    from homebrew_as_code.beerxml_cross_app import main
    s = tmp_path / 'source.xml'
    s.write_text('<RECIPES><RECIPE/></RECIPES>')
    assert main(['--source-xml', str(s), '--reexport-xml', str(s), '--report', str(tmp_path / 'report.json')]) == 1
