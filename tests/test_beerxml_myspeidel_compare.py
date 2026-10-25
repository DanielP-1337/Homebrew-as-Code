import json
import pytest
from homebrew_as_code.beerxml_myspeidel_compare import report
from test_beerxml_v1 import run


def test_manual_comparison_preserves_uncertainty():
    xml, _ = run(emit_target_og=True)
    r = report(xml, {'batch_size_l':20, 'og_sg':1.05684, 'bitterness_ibu':31.5,
                     'mash_in_c':63, 'yeast_amount_g':11.5})
    fields = r['fields']
    assert fields['batch_size_l']['status'] == 'MATCH'
    assert fields['og_sg']['status'] == 'MATCH'
    assert fields['bitterness_ibu']['status'] == 'UNVERIFIED_MAPPING_OR_RECALCULATED'
    assert fields['mash_in_c']['status'] == 'UNVERIFIED_MAPPING_OR_RECALCULATED'
    assert fields['yeast_amount_g']['status'] == 'MATCH'
    assert fields['color_ebc']['status'] == 'NOT_OBSERVED'


def test_reject_unknown_manual_fields():
    xml, _ = run()
    with pytest.raises(ValueError, match='Unknown observation'):
        report(xml, {'token': 'secret'})


def test_reject_invalid_number():
    xml, _ = run()
    with pytest.raises(ValueError):
        report(xml, {'batch_size_l': 'NaN'})
