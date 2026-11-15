"""Map owned service errors to native HA translation keys, retaining API compatibility."""
import json
import re
from pathlib import Path

from homeassistant.exceptions import HomeAssistantError

_SOURCE = json.loads((Path(__file__).parent / "message_sources.json").read_text(encoding="utf-8"))
_PATTERNS = []
for _key, _template in _SOURCE.items():
    if _key.startswith("runtime."):
        _names = re.findall(r"\{(\w+)\}", _template)
        _pattern = re.compile("^" + "(.*?)".join(re.escape(part) for part in re.split(r"\{\w+\}", _template)) + "$", re.DOTALL)
        _PATTERNS.append((_key.replace(".", "_"), _pattern, _names))


def service_error(error):
    """HA translates the message for native action dialogs; external errors stay intact."""
    for key, pattern, names in _PATTERNS:
        if match := pattern.fullmatch(str(error)):
            return HomeAssistantError(translation_domain="hbac", translation_key=key,
                                      translation_placeholders=dict(zip(names, match.groups())))
    return HomeAssistantError(str(error))
