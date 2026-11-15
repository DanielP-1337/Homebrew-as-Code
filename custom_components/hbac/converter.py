"""Pure Brewfather v2 -> Braumeister program conversion, without I/O."""
import math
import unicodedata
from copy import deepcopy


class ConversionError(ValueError):
    """A source value cannot be represented by the controller."""


def integer(value, low, high, field):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value != int(value) or not low <= value <= high):
        raise ConversionError(f"{field}: ganze Zahl zwischen {low} und {high} erforderlich.")
    return int(value)


def convert(source, kind, source_id, mash_in=None, boil_temperature=103):
    """Project a recipe or the batch's own recipe; never substitute a parent."""
    if kind not in ("recipes", "batches") or not isinstance(source, dict):
        raise ConversionError("Ungültiger Brewfather-Datensatz.")
    recipe = source.get("recipe") if kind == "batches" else source
    if not isinstance(recipe, dict):
        raise ConversionError("Der Batch enthält kein vollständiges Rezept.")
    original = recipe.get("name")
    if not isinstance(original, str) or not original.strip():
        raise ConversionError("Rezeptname fehlt.")
    name = original.strip()
    for old, new in {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}.items():
        name = name.replace(old, new)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = "".join(c for c in name if 32 <= ord(c) <= 126 and c != ";").strip()[:14].rstrip()
    if not name:
        raise ConversionError("Rezeptname enthält keine für das Gerät nutzbaren Zeichen.")
    warnings = []
    if name != original:
        warnings.append(f"Gerätename: {original} → {name}")
    mash = recipe.get("mash")
    steps = mash.get("steps") if isinstance(mash, dict) else None
    if not isinstance(steps, list) or not 1 <= len(steps) <= 5:
        raise ConversionError("Das Gerät benötigt 1 bis 5 Maischerasten.")
    rests = []
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            raise ConversionError(f"Rast {index}: ungültige Daten.")
        if step.get("type") not in (None, "Temperature", "Infusion"):
            raise ConversionError(f"Rast {index}: Rasttyp {step.get('type')} wird nicht unterstützt.")
        temp = integer(step.get("stepTemp"), 20, 80, f"Rast {index}, Temperatur")
        minutes = integer(step.get("stepTime"), 1, 180, f"Rast {index}, Minuten")
        if step.get("rampTime") not in (None, 0):
            warnings.append(f"Rast {index}: Rampenzeit nicht übertragen; das Gerät regelt die Aufheizung.")
        if step.get("endTemp") not in (None, temp):
            raise ConversionError(f"Rast {index}: abweichende Endtemperatur ist nicht darstellbar.")
        if step.get("infuseAmount"):
            warnings.append(f"Rast {index}: Infusionswassermenge nicht übertragen.")
        rests.append({"temperature": temp, "minutes": minutes})
    if mash_in is None:
        mash_in = rests[0]["temperature"]
        warnings.append("Einmaischtemperatur aus erster Rast vorgeschlagen; bei Bedarf in HA ändern.")
    else:
        warnings.append("Einmaischtemperatur in HA vorgegeben.")
    duration = integer(recipe.get("boilTime"), 1, 180, "Kochdauer")
    alarms = []
    hops = recipe.get("hops", [])
    if not isinstance(hops, list):
        raise ConversionError("Hopfengaben müssen eine Liste sein.")
    for hop in hops:
        if not isinstance(hop, dict):
            raise ConversionError("Ungültige Hopfengabe.")
        use, label = hop.get("use"), str(hop.get("name", "Hopfen"))
        if use == "Boil":
            if hop.get("timeUnit") not in (None, "min"):
                raise ConversionError(f"{label}: Kochhopfen-Zeit muss in Minuten vorliegen.")
            if hop.get("time") == 0 and not isinstance(hop.get("time"), bool):
                warnings.append(f"{label}: Flameout-Gabe bei 0 Minuten nicht als Gerätealarm übertragen.")
                continue
            alarms.append(integer(hop.get("time"), 1, duration, f"{label}, Restkochzeit"))
        elif use in ("Dry Hop", "Aroma", "Whirlpool", "Mash", "First Wort"):
            warnings.append(f"{label}: {use} nicht als Kochhopfenalarm übertragen.")
        else:
            raise ConversionError(f"{label}: unbekannte Hopfenverwendung {use!r}.")
    unique_alarms = sorted(set(alarms), reverse=True)
    if len(unique_alarms) != len(alarms):
        warnings.append("Gleichzeitige Kochhopfengaben zu einem Gerätealarm zusammengefasst.")
    if len(unique_alarms) > 6:
        raise ConversionError("Mehr als sechs unterschiedliche Kochhopfen-Zeitpunkte.")
    warnings.append("Kochtemperatur ist ein Geräteparameter (Vorgabe 103 °C), in HA änderbar.")
    program = {
        "name": name,
        "mash_in_temperature": integer(mash_in, 20, 80, "Einmaischtemperatur"),
        "rests": rests,
        "boil_minutes": duration,
        "boil_temperature": integer(boil_temperature, 95, 105, "Kochtemperatur"),
        "hop_additions": unique_alarms,
    }
    return {"program": program, "source": {"kind": kind, "id": source_id, "name": original,
            "batch_no": source.get("batchNo") if kind == "batches" else None},
            "warnings": warnings,
            "not_transferred": ["Zutaten und Mengen", "Wasser und Wasserchemie", "Gärung und Abfüllung",
                                "Zielwerte und Messwerte", "Whirlpool, Stopfhopfen und weitere Zutaten"],
            "source_recipe": deepcopy(recipe)}
