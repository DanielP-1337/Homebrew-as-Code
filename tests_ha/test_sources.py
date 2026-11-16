"""Source adapter and import boundary regression tests."""
import base64
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.hbac.api import BrewfatherAuthError, BrewfatherError
from custom_components.hbac.beerxml import (
    MAX_BYTES,
    list_files,
    normalized_recipe,
    parse_beerxml,
    read_file,
)
from custom_components.hbac.brewersfriend import BrewersFriendClient
from custom_components.hbac.converter import ConversionError, convert
from custom_components.hbac.manager import Manager
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.common import MockConfigEntry

RECIPE = '''<RECIPE><NAME>XML Test</NAME><VERSION>1</VERSION><BOIL_TIME>60</BOIL_TIME>
<MASH><VERSION>1</VERSION><MASH_STEPS><MASH_STEP><VERSION>1</VERSION><TYPE>Infusion</TYPE>
<STEP_TEMP>63.0</STEP_TEMP><DISPLAY_STEP_TEMP>145.4 F</DISPLAY_STEP_TEMP><STEP_TIME>40</STEP_TIME>
<INFUSE_AMOUNT>20</INFUSE_AMOUNT></MASH_STEP></MASH_STEPS></MASH>
<HOPS><HOP><VERSION>1</VERSION><NAME>Hop</NAME><USE>Boil</USE><TIME>15</TIME></HOP>
<HOP><VERSION>1</VERSION><NAME>Late</NAME><USE>Boil</USE><TIME>0</TIME></HOP>
<HOP><VERSION>1</VERSION><NAME>Dry</NAME><USE>Dry Hop</USE><TIME>4320</TIME></HOP></HOPS></RECIPE>'''
XML = ('<RECIPES>' + RECIPE + '</RECIPES>').encode()


def test_standard_units_and_multi_recipe():
    nodes = parse_beerxml(('<RECIPES>' + RECIPE * 2 + '</RECIPES>').encode())
    assert len(nodes) == 2
    result = convert(normalized_recipe(nodes[0]), 'recipes', 'xml')
    assert result['program']['rests'] == [{'temperature': 63, 'minutes': 40}]
    assert result['program']['hop_additions'] == [15]
    assert any('Flameout' in w for w in result['warnings'])
    assert any('Dry Hop' in w for w in result['warnings'])
    assert any('Infusionswasser' in w for w in result['warnings'])


@pytest.mark.parametrize('raw', [b'', b'x' * (MAX_BYTES + 1), b'<RECIPES>', b'<RECIPES/>',
    b'<RECIPE/>', ('<RECIPES>' + RECIPE * 101 + '</RECIPES>').encode(),
    b'<!DOCTYPE RECIPES [<!ENTITY x SYSTEM "file:///etc/passwd">]><RECIPES>&x;</RECIPES>',
    b'<!DOCTYPE RECIPES><RECIPES/>'])
def test_invalid_and_unsafe_xml_rejected(raw):
    with pytest.raises(ConversionError):
        parse_beerxml(raw)


@pytest.mark.parametrize('old,new', [('63.0', '63.5'), ('63.0', 'nan'), ('63.0', '145.4'),
    ('<STEP_TIME>40</STEP_TIME>', ''), ('Infusion', 'Decoction'), ('<VERSION>1</VERSION>', '<VERSION>2</VERSION>'),
    ('<BOIL_TIME>60</BOIL_TIME>', '<BOIL_TIME>60</BOIL_TIME><BOIL_TIME>90</BOIL_TIME>')])
def test_no_silent_rounding_or_unsupported_program(old, new):
    with pytest.raises(ConversionError):
        convert(normalized_recipe(parse_beerxml(XML.replace(old.encode(), new.encode()))[0]), 'recipes', 'xml')


def test_legacy_xml_encoding():
    raw = b'<?xml version="1.0" encoding="ISO-8859-1"?>' + XML.replace(b'XML Test', b'M\xe4rzen')
    assert normalized_recipe(parse_beerxml(raw)[0])['name'] == 'Märzen'


def test_folder_read_only_and_traversal(tmp_path):
    folder = tmp_path / 'import'
    folder.mkdir()
    file = folder / 'recipe.xml'
    file.write_bytes(XML)
    (folder / 'secret.txt').write_text('secret')
    assert list_files(folder) == [{'id': 'recipe.xml', 'name': 'recipe.xml'}]
    assert len(read_file(folder, 'recipe.xml')) == 1
    assert file.read_bytes() == XML
    for name in ('../recipe.xml', '/etc/passwd', 'secret.txt', '..\\recipe.xml'):
        with pytest.raises(ConversionError):
            read_file(folder, name)
    (folder / 'link.xml').symlink_to(file)
    with pytest.raises(ConversionError):
        read_file(folder, 'link.xml')
    assert len(list_files(folder)) == 1


@pytest.fixture
async def import_manager(hass, tmp_path):
    entry = MockConfigEntry(domain='hbac', data={'bridge_entry_id': 'bridge', 'import_directory': str(tmp_path)})
    entry.add_to_hass(hass)
    manager = Manager(hass, entry, None)
    manager.store.async_save = AsyncMock()
    manager.bridge = AsyncMock()
    return manager


async def test_file_snapshot_survives_source_change_and_no_device_calls(import_manager, tmp_path):
    path = tmp_path / 'one.xml'
    path.write_bytes(XML)
    files = await import_manager.dispatch('catalog', {'kind': 'beerxml_folder'})
    assert files['items'][0]['id'] == 'one.xml'
    items = await import_manager.dispatch('open_file', {'filename': 'one.xml'})
    path.write_bytes(b'changed after import')
    preview = await import_manager.dispatch('preview', {'kind': 'beerxml_folder', 'source_id': items['items'][0]['id']})
    assert preview['program']['rests'][0]['temperature'] == 63
    await import_manager.dispatch('add', {'preview_id': preview['preview_id'], 'revision': import_manager.revision})
    assert import_manager.queue[0]['source']['kind'] == 'beerxml_folder'
    import_manager.bridge.assert_not_awaited()


async def test_browser_upload_multi_selection_and_overrides(import_manager):
    raw = ('<RECIPES>' + RECIPE + RECIPE.replace('XML Test', 'Second') + '</RECIPES>').encode()
    result = await import_manager.dispatch('import_file', {'content': base64.b64encode(raw).decode()})
    assert len(result['items']) == 2
    preview = await import_manager.dispatch('preview', {'kind': 'beerxml_upload', 'source_id': result['items'][1]['id'], 'mash_in': 55, 'boil_temperature': 100})
    assert preview['program']['name'] == 'Second'
    assert preview['program']['mash_in_temperature'] == 55
    assert preview['program']['boil_temperature'] == 100
    import_manager.bridge.assert_not_awaited()
    with pytest.raises(ValueError, match='expired'):
        await import_manager.dispatch('preview', {'kind': 'beerxml_folder', 'source_id': result['items'][0]['id']})
    with pytest.raises(ValueError):
        await import_manager.dispatch('import_file', {'content': 'not base64!!'})


async def test_brewersfriend_catalog_and_xml(hass, aioclient_mock):
    client = BrewersFriendClient(async_get_clientsession(hass), 'private-key')
    aioclient_mock.get('https://api.brewersfriend.com/v1/recipes', json={'recipes': [{'id': '42', 'title': 'Example'}]})
    aioclient_mock.get('https://api.brewersfriend.com/v1/recipes/42.xml', content=XML)
    assert await client.catalog() == [{'id': '42', 'name': 'Example'}]
    recipe = await client.get('brewersfriend', '42')
    assert recipe['mash']['steps'][0]['stepTemp'] == 63
    assert aioclient_mock.mock_calls[0][3]['X-API-KEY'] == 'private-key'


@pytest.mark.parametrize('status', [401, 403, 404, 429, 500, 302])
async def test_brewersfriend_failures_do_not_expose_key(hass, aioclient_mock, status):
    client = BrewersFriendClient(async_get_clientsession(hass), 'secret-key')
    aioclient_mock.get('https://api.brewersfriend.com/v1/recipes', status=status, text='secret-key', headers={'Location': 'https://example.com'})
    with pytest.raises(BrewfatherError) as error:
        await client.page()
    assert 'secret-key' not in str(error.value)
    assert aioclient_mock.call_count == 1
    if status == 429:
        with pytest.raises(BrewfatherError):
            await client.page()
        assert aioclient_mock.call_count == 1


async def test_brewersfriend_invalid_id_without_request(hass, aioclient_mock):
    client = BrewersFriendClient(async_get_clientsession(hass), 'key')
    with pytest.raises(BrewfatherError):
        await client.get('brewersfriend', '../42')
    assert aioclient_mock.call_count == 0


async def test_brewersfriend_pagination_and_repeated_page(hass):
    client = BrewersFriendClient(async_get_clientsession(hass), 'key')
    page = [{'id': str(i), 'title': str(i)} for i in range(100)]
    client.page = AsyncMock(side_effect=[page, [{'id': '100', 'title': 'Last'}]])
    assert len(await client.catalog()) == 101
    assert client.page.call_args_list[1].args == (100,)
    client.page = AsyncMock(side_effect=[page, page])
    with pytest.raises(BrewfatherError):
        await client.catalog()


async def test_beerxml_only_config_and_provider_validation(hass):
    from custom_components.hbac.config_flow import HbacConfigFlow
    flow = HbacConfigFlow()
    flow.hass = hass
    assert await flow.validate({}) == {}
    assert await flow.validate({'user_id': 'alone'}) == {'base': 'incomplete_brewfather'}
    assert await flow.validate({'import_directory': 'relative'}) == {'base': 'invalid_directory'}
    with patch('custom_components.hbac.config_flow.BrewersFriendClient.page', AsyncMock(side_effect=BrewfatherAuthError())):
        assert await flow.validate({'brewersfriend_api_key': 'bad'}) == {'brewersfriend_api_key': 'invalid_auth'}

async def test_file_only_setup_and_service_import(hass):
    from homeassistant.setup import async_setup_component
    entry = MockConfigEntry(domain='hbac', data={'bridge_entry_id': 'bridge'})
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, 'hbac', {})
    await hass.async_block_till_done()
    manager = hass.data['hbac'][entry.entry_id]
    assert manager.state()['sources'] == ['beerxml_folder', 'beerxml_upload']
    result = await hass.services.async_call('hbac', 'import_file',
        {'content': base64.b64encode(XML).decode()}, blocking=True, return_response=True)
    assert result['items'][0]['name'] == 'XML Test'
    assert not manager.queue and not manager.job
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_add_brewersfriend_to_existing_entry(hass):
    entry = MockConfigEntry(domain='hbac', data={'bridge_entry_id': 'bridge', 'user_id': 'u', 'api_key': 'old'})
    entry.add_to_hass(hass)
    with patch('custom_components.hbac.config_flow.BrewfatherClient.get', AsyncMock(return_value=[])), patch(
        'custom_components.hbac.config_flow.BrewersFriendClient.page', AsyncMock(return_value=[])), patch(
        'homeassistant.config_entries.ConfigEntries.async_reload', AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_init('hbac', context={'source': 'reconfigure', 'entry_id': entry.entry_id})
        result = await hass.config_entries.flow.async_configure(result['flow_id'], {
            'user_id': 'u', 'api_key': 'old', 'brewersfriend_api_key': 'bf-key', 'import_directory': '/config/hbac/import'})
        assert result['type'] == 'abort'
        assert entry.data['api_key'] == 'old'
        assert entry.data['brewersfriend_api_key'] == 'bf-key'
        assert entry.data['bridge_entry_id'] == 'bridge'


@pytest.mark.parametrize('body', [b'not json', b'{"recipes":{}}', b'x' * (MAX_BYTES + 1)])
async def test_brewersfriend_response_bounds(hass, aioclient_mock, body):
    client = BrewersFriendClient(async_get_clientsession(hass), 'key')
    aioclient_mock.get('https://api.brewersfriend.com/v1/recipes', content=body)
    with pytest.raises(BrewfatherError):
        await client.page()

async def test_brewersfriend_empty_account_is_valid_in_setup_and_catalog(hass, aioclient_mock):
    from custom_components.hbac.config_flow import HbacConfigFlow
    aioclient_mock.get('https://api.brewersfriend.com/v1/recipes', status=404,
                      json={'message': 'not-found', 'detail': 'no recipes found'})
    client = BrewersFriendClient(async_get_clientsession(hass), 'test-key')
    assert await client.catalog() == []
    flow = HbacConfigFlow()
    flow.hass = hass
    assert await flow.validate({'brewersfriend_api_key': 'test-key'}) == {}


@pytest.mark.parametrize('suffix,payload', [
    ('', {'message': 'not-found', 'detail': 'unknown route'}),
    ('', {'message': 'unauthorized', 'detail': 'no recipes found'}),
    ('/42.xml', {'message': 'not-found', 'detail': 'no recipes found'}),
])
async def test_other_404s_are_not_empty_libraries(hass, aioclient_mock, suffix, payload):
    aioclient_mock.get('https://api.brewersfriend.com/v1/recipes' + suffix, status=404, json=payload)
    client = BrewersFriendClient(async_get_clientsession(hass), 'test-key')
    with pytest.raises(BrewfatherError, match='HTTP 404'):
        await client.request(suffix)


async def test_setup_error_identifies_provider_and_safe_log(hass, caplog):
    from custom_components.hbac.config_flow import HbacConfigFlow
    flow = HbacConfigFlow()
    flow.hass = hass
    with patch('custom_components.hbac.config_flow.BrewfatherClient.get', AsyncMock(return_value=[])), patch(
        'custom_components.hbac.config_flow.BrewersFriendClient.page',
        AsyncMock(side_effect=BrewfatherError("Brewer's Friend: request failed (HTTP 500)."))):
        assert await flow.validate({'user_id': 'u', 'api_key': 'bf-secret', 'brewersfriend_api_key': 'other-secret'}) == {
            'brewersfriend_api_key': 'cannot_connect'}
    assert 'HTTP 500' in caplog.text
    assert 'bf-secret' not in caplog.text and 'other-secret' not in caplog.text
