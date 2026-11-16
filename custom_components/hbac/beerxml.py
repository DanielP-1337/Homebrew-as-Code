"""Bounded BeerXML v1 import into the shared recipe conversion model."""
import math
from pathlib import Path

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from .converter import ConversionError

MAX_BYTES = 512 * 1024
MAX_RECIPES = 100


def parse_beerxml(raw):
    """Read standard Celsius/minute fields, never DISPLAY_* values or XML entities."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ConversionError("BeerXML: empty file or file larger than 512 KiB.")
    try:
        root = ET.fromstring(raw, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    except (ET.ParseError, DefusedXmlException, ValueError) as err:
        raise ConversionError("BeerXML: invalid or unsafe XML.") from err
    if root.tag != "RECIPES":
        raise ConversionError("BeerXML: expected RECIPES with 1 to 100 recipes.")
    recipes = root.findall("RECIPE")
    if not 1 <= len(recipes) <= MAX_RECIPES:
        raise ConversionError("BeerXML: expected RECIPES with 1 to 100 recipes.")
    # Each record is validated when selected, so one unsupported recipe does not
    # prevent importing a different recipe from the same file.
    return recipes


def normalized_recipe(node):
    def text(parent, key, required=True):
        elements = parent.findall(key)
        if len(elements) > 1 or (required and (not elements or not (elements[0].text or "").strip())):
            raise ConversionError(f"BeerXML: missing or duplicate field {key}.")
        return (elements[0].text or "").strip() if elements else None

    def number(parent, key, required=True):
        value = text(parent, key, required)
        # Exporters may emit an empty element instead of omitting an optional
        # value. Keep that distinct from zero; required fields stay strict.
        if value is None or (not required and value == ""):
            return None
        try:
            result = float(value)
            if not math.isfinite(result):
                raise ValueError
            return result
        except ValueError as err:
            raise ConversionError(f"BeerXML: invalid number in {key}.") from err

    def version(parent):
        if text(parent, "VERSION") != "1":
            raise ConversionError("BeerXML: only version 1 is supported.")

    def container(parent, key):
        nodes = parent.findall(key)
        if len(nodes) != 1:
            raise ConversionError(f"BeerXML: missing or duplicate field {key}.")
        return nodes[0]

    version(node)
    mash = container(node, "MASH")
    version(mash)
    steps = []
    for step in container(mash, "MASH_STEPS").findall("MASH_STEP"):
        version(step)
        steps.append({"name": text(step, "NAME", False) or "", "type": text(step, "TYPE"), "stepTemp": number(step, "STEP_TEMP"),
                      "stepTime": number(step, "STEP_TIME"), "rampTime": number(step, "RAMP_TIME", False),
                      "endTemp": number(step, "END_TEMP", False), "infuseAmount": number(step, "INFUSE_AMOUNT", False)})
    hops = []
    for hop in container(node, "HOPS").findall("HOP"):
        version(hop)
        hops.append({"name": text(hop, "NAME"), "use": text(hop, "USE"),
                     "time": number(hop, "TIME"), "timeUnit": "min"})
    return {"name": text(node, "NAME"), "boilTime": number(node, "BOIL_TIME"),
            "mash": {"steps": steps}, "hops": hops}


def import_directory(hass, configured=None):
    """The administrator chooses a directory; callers can only select its XML files."""
    return Path(configured or hass.config.path("hbac", "import")).expanduser().resolve()


def list_files(directory):
    try:
        if not directory.exists():
            return []
        return [{"id": p.name, "name": p.name} for p in sorted(directory.iterdir())
                if p.suffix.lower() == ".xml" and not p.is_symlink() and p.is_file()
                and p.resolve().parent == directory][:500]
    except OSError as err:
        raise ConversionError("BeerXML: import folder is not accessible.") from err


def read_file(directory, filename):
    if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise ConversionError("BeerXML: invalid file selection.")
    path = directory / filename
    if path.suffix.lower() != ".xml" or path.is_symlink() or path.resolve().parent != directory:
        raise ConversionError("BeerXML: invalid file selection.")
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError as err:
        raise ConversionError("BeerXML: file is not accessible.") from err
    return parse_beerxml(raw)
