"""Read-only, privacy-preserving inspection of MySpeidel recipe structures."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .myspeidel import MySpeidelClient, MySpeidelError, inspect_structure
from .recipe import load_recipe


def private_recipes(client: MySpeidelClient, machine_size: int = 20) -> list[dict[str, Any]]:
    """Return only private recipes for the requested machine size."""
    response = client.list_recipes(machine_size=machine_size, include_public=False)
    if not isinstance(response, Mapping) or not isinstance(response.get("collection"), list):
        raise MySpeidelError("Unexpected recipe collection structure")
    result = []
    for item in response["collection"]:
        if not isinstance(item, dict):
            continue
        machine = item.get("machine_type")
        if not isinstance(machine, dict) or machine.get("size") != machine_size:
            continue
        # 'public' is numeric in the observed API response: 0 means private.
        if item.get("public") not in (0, False):
            continue
        uuid = item.get("uuid")
        if not isinstance(uuid, str):
            continue
        result.append(item)
    return result


def inspect_recipe(client: MySpeidelClient, recipe_meta: Mapping[str, Any],
                   machine_size: int = 20) -> dict[str, Any]:
    """Fetch exactly one selected UUID, returning only schemas and local comparisons."""
    machine = recipe_meta.get("machine_type")
    if not isinstance(machine, Mapping) or machine.get("size") != machine_size:
        raise MySpeidelError("Selected recipe has a different machine size")
    if recipe_meta.get("public") not in (0, False):
        raise MySpeidelError("Selected recipe is not private")
    uuid = recipe_meta.get("uuid")
    if not isinstance(uuid, str):
        raise MySpeidelError("Selected recipe has no UUID")
    detail = client.get_recipe(uuid)  # GET-only; client validates UUID
    # Do not return detail, identifier, names, or content values.
    return {
        "machine_size_verified_from_collection": True,
        "collection_schema_version_type": type(recipe_meta.get("schema_version")).__name__,
        "collection_content_version_type": type(recipe_meta.get("content_version")).__name__,
        "detail_structure": inspect_structure(detail, max_depth=12),
    }


def local_recipe_inventory(path: str) -> dict[str, Any]:
    """Show local recipe section names/counts, not private cloud field values."""
    recipe = load_recipe(path)
    mash = recipe["mash"]
    boil = recipe["boil"]
    return {
        "local_sections": sorted(recipe.keys()),
        "mash_step_count": len(mash["steps"]),
        "boil_addition_count": len(boil.get("additions", [])),
        "mapping_status": "NOT_IMPLEMENTED: compare types/fields before creating a writer",
    }
