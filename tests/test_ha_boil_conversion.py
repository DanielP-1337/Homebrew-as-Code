"""Offline source conversion checks; no Home Assistant or source accounts required."""
import importlib.util
import sys
import types
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'hbac'
PACKAGE = '_hbac_boil_tests'
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = package


def load(name):
    spec = importlib.util.spec_from_file_location(f'{PACKAGE}.{name}', ROOT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


converter = load('converter')
beerxml = load('beerxml')


@pytest.fixture(params=['brewfather', 'brewersfriend_beerxml'])
def source(request):
    if request.param == 'brewfather':
        return {'name': 'Test', 'boilTime': 60, 'mash': {'steps': [
            {'type': 'Infusion', 'stepTemp': 63, 'stepTime': 40}]}, 'hops': []}
    raw = b'''<RECIPES><RECIPE><VERSION>1</VERSION><NAME>Test</NAME><BOIL_TIME>60</BOIL_TIME>
    <MASH><VERSION>1</VERSION><MASH_STEPS><MASH_STEP><VERSION>1</VERSION><TYPE>Infusion</TYPE>
    <STEP_TEMP>63</STEP_TEMP><DISPLAY_STEP_TEMP>145.4 F</DISPLAY_STEP_TEMP>
    <STEP_TIME>40</STEP_TIME></MASH_STEP></MASH_STEPS></MASH>
    <HOPS/></RECIPE></RECIPES>'''
    return beerxml.normalized_recipe(beerxml.parse_beerxml(raw)[0])


@pytest.mark.parametrize('temperature', [None, 100, 103])
def test_supported_setpoints_preserve_source(source, temperature):
    before = deepcopy(source)
    options = {} if temperature is None else {'boil_temperature': temperature}
    result = converter.convert(source, 'recipes', 'test', **options)['program']
    assert result['boil_temperature'] == (103 if temperature is None else temperature)
    assert result['rests'] == [{'temperature': 63, 'minutes': 40}]
    assert result['boil_minutes'] == 60
    assert source == before


@pytest.mark.parametrize('temperature', [104, 105])
def test_excess_setpoints_rejected_without_clamping(source, temperature):
    before = deepcopy(source)
    with pytest.raises(converter.ConversionError, match='103'):
        converter.convert(source, 'recipes', 'test', boil_temperature=temperature)
    assert source == before
