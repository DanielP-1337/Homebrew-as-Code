from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.hbac import async_setup
from custom_components.hbac.api import (
    BrewfatherAuthError,
    BrewfatherClient,
    BrewfatherError,
)
from custom_components.hbac.converter import ConversionError, convert
from custom_components.hbac.manager import Manager
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry


def recipe():
    return {"_id": "r1", "name": "Märzen Test", "boilTime": 60,
            "mash": {"steps": [{"type": "Temperature", "stepTemp": 63, "stepTime": 40},
                               {"type": "Temperature", "stepTemp": 78, "stepTime": 10}]},
            "hops": [{"name": "A", "use": "Boil", "time": 60},
                     {"name": "B", "use": "Boil", "time": 15},
                     {"name": "C", "use": "Dry Hop", "time": 3, "timeUnit": "days"}]}


def test_batch_snapshot_and_no_mutation():
    original = recipe()
    batch = {"recipe": deepcopy(original), "batchNo": 7, "measuredBoilTime": 90}
    batch["recipe"]["boilTime"] = 45
    batch["recipe"]["hops"][0]["time"] = 45
    before = deepcopy(batch)
    result = convert(batch, "batches", "b7")
    assert result["program"] == {"name": "Maerzen Test", "mash_in_temperature": 63,
        "rests": [{"temperature": 63, "minutes": 40}, {"temperature": 78, "minutes": 10}],
        "boil_minutes": 45, "boil_temperature": 103, "hop_additions": [45, 15]}
    assert batch == before
    assert original["boilTime"] == 60
    assert result["source"]["batch_no"] == 7
    assert any("Dry Hop" in w for w in result["warnings"])


@pytest.mark.parametrize("value", [None, True, 19, 81, 63.5, float("nan"), float("inf")])
def test_invalid_mash_temperature(value):
    source = recipe()
    source["mash"]["steps"][0]["stepTemp"] = value
    with pytest.raises(ConversionError):
        convert(source, "recipes", "r")


@pytest.mark.parametrize("count", [0, 6])
def test_rest_capacity(count):
    source = recipe()
    source["mash"]["steps"] = source["mash"]["steps"][:1] * count
    with pytest.raises(ConversionError):
        convert(source, "recipes", "r")


def test_alarm_grouping_flameout_and_override():
    source = recipe()
    source["hops"] = [{"name": "A", "use": "Boil", "time": t} for t in [0, 15, 60, 15]]
    result = convert(source, "recipes", "r", 55, 100)
    assert result["program"]["hop_additions"] == [60, 15]
    assert result["program"]["mash_in_temperature"] == 55
    assert result["program"]["boil_temperature"] == 100
    assert any("Flameout" in w for w in result["warnings"])
    source["hops"] = [{"name": "A", "use": "Boil", "time": t} for t in range(1, 8)]
    with pytest.raises(ConversionError):
        convert(source, "recipes", "r")


@pytest.mark.parametrize("field,value", [("type", "Decoction"), ("endTemp", 70), ("stepTime", 0)])
def test_unsupported_rest(field, value):
    source = recipe()
    source["mash"]["steps"][0][field] = value
    with pytest.raises(ConversionError):
        convert(source, "recipes", "r")


def test_missing_batch_recipe_and_unknown_hop():
    with pytest.raises(ConversionError):
        convert({"recipeId": "r"}, "batches", "b")
    source = recipe()
    source["hops"][0]["use"] = "Unknown"
    with pytest.raises(ConversionError):
        convert(source, "recipes", "r")


@pytest.fixture
async def manager(hass):
    entry = MockConfigEntry(domain="hbac", data={"bridge_entry_id": "bridge", "user_id": "u", "api_key": "secret"})
    entry.add_to_hass(hass)
    manager = Manager(hass, entry, AsyncMock())
    manager.client.get.return_value = recipe()
    manager.store.async_save = AsyncMock()
    hass.data["hbac"] = {entry.entry_id: manager}
    async def readiness(call):
        assert call.data["config_entry_id"] == "bridge"
        return {"ready_for_upload": True}
    async def start(call):
        assert manager.store.async_save.await_count >= 2
        assert manager.job["result"] == "submitting"
        return {"job_id": "job-1", "result": "queued", "written": 0}
    async def status(call):
        assert call.data["job_id"] == "job-1"
        return {"job_id": "job-1", "result": "confirmed", "written": 1, "content_verification": "matched"}
    for name, handler in [("recipe_upload_readiness", readiness), ("start_recipe_upload", start), ("recipe_upload_status", status)]:
        hass.services.async_register("speidel_braumeister", name, handler, supports_response=SupportsResponse.ONLY)
    return manager


async def add(manager):
    preview = await manager.dispatch("preview", {"kind": "recipes", "source_id": "r1"})
    assert "source_recipe" not in preview
    await manager.dispatch("add", {"preview_id": preview["preview_id"], "revision": manager.revision})


async def test_real_ha_service_workflow(hass, manager, hass_client):
    from homeassistant.setup import async_setup_component
    await async_setup_component(hass, "http", {})
    with patch.object(hass.http, "async_register_static_paths", AsyncMock()):
        await async_setup(hass, {})
    async def call(action, data=None):
        return await hass.services.async_call("hbac", action, data or {}, blocking=True, return_response=True)
    preview = await call("preview", {"kind": "recipes", "source_id": "r1"})
    state = await call("add", {"preview_id": preview["preview_id"], "revision": manager.revision})
    assert "source_recipe" not in state["queue"][0]
    state = await call("upload", {"revision": state["revision"], "replace_all": True})
    assert state["job"]["job_id"] == "job-1"
    state = await call("status")
    assert state["job"]["content_verification"] == "matched"


async def test_readiness_blocks_write(hass, manager):
    await add(manager)
    async def blocked(call):
        return {"ready_for_upload": False, "blocking_reasons": ["device_not_idle"]}
    hass.services.async_register("speidel_braumeister", "recipe_upload_readiness", blocked, supports_response=SupportsResponse.ONLY)
    with pytest.raises(HomeAssistantError, match="device_not_idle"):
        await manager.dispatch("upload", {"revision": manager.revision, "replace_all": True})
    assert manager.job is None


async def test_lost_response_never_resubmits(hass, manager):
    await add(manager)
    counter = []
    async def lost(call):
        counter.append(1)
        raise HomeAssistantError("Connection lost")
    hass.services.async_register("speidel_braumeister", "start_recipe_upload", lost, supports_response=SupportsResponse.ONLY)
    for _ in range(2):
        with pytest.raises(HomeAssistantError):
            await manager.dispatch("upload", {"revision": manager.revision, "replace_all": True})
    assert len(counter) == 1
    assert manager.job["result"] == "outcome_unknown"
    restored = Manager(hass, manager.entry, manager.client)
    restored.store.async_load = AsyncMock(return_value={"queue": manager.queue, "revision": manager.revision,
                                                      "job": {"result": "submitting"}})
    restored.store.async_save = AsyncMock()
    await restored.load()
    assert restored.job["result"] == "outcome_unknown"


async def test_stale_revision_and_confirmation(manager):
    await add(manager)
    for data in [{"revision": "old", "replace_all": True}, {"revision": manager.revision, "replace_all": False}]:
        with pytest.raises(HomeAssistantError):
            await manager.dispatch("upload", data)
    assert manager.job is None


async def test_expired_job_is_not_success(manager):
    await add(manager)
    await manager.dispatch("upload", {"revision": manager.revision, "replace_all": True})
    manager.bridge = AsyncMock(side_effect=HomeAssistantError("expired"))
    with pytest.raises(HomeAssistantError):
        await manager.dispatch("status", {})
    assert manager.job["result"] == "queued"
    with pytest.raises(HomeAssistantError):
        await manager.dispatch("upload", {"revision": manager.revision, "replace_all": True})


async def test_queue_order_capacity_and_collisions(manager):
    for i in range(9):
        source = recipe()
        source["name"] = f"Recipe {i}"
        manager.client.get.return_value = source
        await add(manager)
    with pytest.raises(HomeAssistantError):
        await add(manager)
    await manager.dispatch("move", {"index": 8, "target": 0, "revision": manager.revision})
    assert manager.queue[0]["program"]["name"] == "Recipe 8"
    await manager.dispatch("remove", {"index": 0, "revision": manager.revision})
    manager.client.get.return_value = recipe()
    manager.client.get.return_value["name"] = "Recipe 0"
    with pytest.raises(HomeAssistantError, match="Gerätename"):
        await add(manager)


async def test_client_pagination():
    client = BrewfatherClient(None, "u", "k")
    client.get = AsyncMock(side_effect=[[{"_id": str(i), "name": str(i)} for i in range(50)], [{"_id": "50", "name": "Last"}]])
    rows = await client.catalog("recipes")
    assert len(rows) == 51
    assert client.get.call_args.kwargs["start_after"] == "49"


@pytest.mark.parametrize("status,error", [(401, BrewfatherAuthError), (403, BrewfatherAuthError), (404, BrewfatherError), (429, BrewfatherError), (302, BrewfatherError)])
async def test_client_http_errors(aioclient_mock, hass, status, error):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    client = BrewfatherClient(async_get_clientsession(hass), "u", "secret")
    aioclient_mock.get("https://api.brewfather.app/v2/recipes/r1", status=status, headers={"Retry-After": "60"})
    with pytest.raises(error) as exc:
        await client.get("recipes", "r1")
    assert "secret" not in str(exc.value)
    if status == 429:
        with pytest.raises(BrewfatherError):
            await client.get("recipes", "r1")
        assert aioclient_mock.call_count == 1


async def test_config_flow(hass):
    bridge = MockConfigEntry(domain="speidel_braumeister", title="Braumeister", data={})
    bridge.add_to_hass(hass)
    with patch("custom_components.hbac.config_flow.BrewfatherClient.get", AsyncMock(return_value=[])), patch(
            "custom_components.hbac.async_setup_entry", AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_init("hbac", context={"source": "user"})
        assert result["type"] == "form"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {
            "user_id": "u", "api_key": "secret", "bridge_entry_id": bridge.entry_id})
        assert result["type"] == "create_entry"
        await hass.async_block_till_done()


async def test_full_entry_setup_sensor_and_unload(hass):
    from homeassistant.setup import async_setup_component
    entry = MockConfigEntry(domain="hbac", title="HBAC Test", data={
        "bridge_entry_id": "bridge", "user_id": "u", "api_key": "secret"})
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "hbac", {})
    await hass.async_block_till_done()
    state = next(s for s in hass.states.async_all("sensor") if s.attributes.get("entry_id") == entry.entry_id)
    assert state.state == "idle"
    assert "secret" not in str(state.attributes)
    assert hass.services.has_service("hbac", "preview")
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.entry_id not in hass.data["hbac"]


async def test_reconfigure_updates_credentials(hass):
    entry = MockConfigEntry(domain="hbac", data={"bridge_entry_id": "bridge", "user_id": "u", "api_key": "old"})
    entry.add_to_hass(hass)
    with patch("custom_components.hbac.config_flow.BrewfatherClient.get", AsyncMock(return_value=[])), patch(
            "homeassistant.config_entries.ConfigEntries.async_reload", AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_init("hbac", context={"source": "reconfigure", "entry_id": entry.entry_id})
        assert result["type"] == "form"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": "u2", "api_key": "new"})
        assert result["type"] == "abort"
        assert entry.data["api_key"] == "new"
        assert entry.data["bridge_entry_id"] == "bridge"


async def test_api_batch_details_and_basic_auth(hass, aioclient_mock):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    client = BrewfatherClient(async_get_clientsession(hass), "u", "secret")
    data = {"recipe": recipe(), "batchNo": 17}
    aioclient_mock.get("https://api.brewfather.app/v2/batches/b17", json=data)
    assert await client.get("batches", "b17") == data
    assert aioclient_mock.call_count == 1


async def test_reload_tracks_existing_job_without_start(hass, manager):
    saved = {"queue": [], "revision": "saved", "job": {"job_id": "job-1", "result": "queued", "started_at": 1}}
    manager.store.async_load = AsyncMock(return_value=saved)
    await manager.load()
    assert manager.job["job_id"] == "job-1"
    result = await manager.dispatch("status", {})
    assert result["job"]["content_verification"] == "matched"


async def test_wrong_job_response_rejected(manager):
    manager.job = {"job_id": "job-1", "result": "queued"}
    manager.bridge = AsyncMock(return_value={"job_id": "other", "result": "confirmed"})
    with pytest.raises(HomeAssistantError):
        await manager.dispatch("status", {})
    assert manager.job["result"] == "queued"


async def test_upload_uses_reviewed_snapshot(manager):
    await add(manager)
    manager.client.get.return_value["mash"]["steps"][0]["stepTemp"] = 50
    await manager.dispatch("upload", {"revision": manager.revision, "replace_all": True})
    assert manager.job["programs"][0]["rests"][0]["temperature"] == 63
    assert manager.client.get.await_count == 1


async def test_state_reads_preserve_error(manager):
    manager.error = "Status nicht abrufbar"
    state = await manager.dispatch("state", {})
    assert state["error"] == "Status nicht abrufbar"


async def test_cancelled_start_leaves_persistent_unknown(hass, manager):
    import asyncio
    await add(manager)
    async def cancelled(call):
        raise asyncio.CancelledError
    hass.services.async_register("speidel_braumeister", "start_recipe_upload", cancelled, supports_response=SupportsResponse.ONLY)
    with pytest.raises(asyncio.CancelledError):
        await manager.dispatch("upload", {"revision": manager.revision, "replace_all": True})
    assert manager.job["result"] == "outcome_unknown"
    assert manager.store.async_save.call_args.args[0]["job"]["result"] == "outcome_unknown"
