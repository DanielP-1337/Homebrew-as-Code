"""Embed the en-US fallback and legacy message patterns; JSON remains authoritative."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components/hbac/frontend"
VERSION = json.loads((FRONTEND.parent / "manifest.json").read_text(encoding="utf-8"))["version"]
fallback = json.loads((FRONTEND / "locales/en-US.json").read_text(encoding="utf-8"))
german = json.loads((FRONTEND.parent / "message_sources.json").read_text(encoding="utf-8"))
patterns = []
for catalog in (german, fallback):
    for key, template in catalog.items():
        if not key.startswith("runtime."):
            continue
        names = re.findall(r"\{(\w+)\}", template)
        pattern = "^" + "(.*?)".join(re.escape(p) for p in re.split(r"\{\w+\}", template)) + "$"
        patterns.append([key, pattern, names])
path = FRONTEND / "hbac-card.js"
source = path.read_text(encoding="utf-8")
if "/* END GENERATED I18N */" in source:
    source = source.split("/* END GENERATED I18N */", 1)[1].lstrip()
header = "/* BEGIN GENERATED I18N: run scripts/build_frontend_i18n.py after editing en-US/message_sources/core */\n"
header += f"const HBAC_VERSION = {json.dumps(VERSION)};\n"
header += "const HBAC_EN_US = " + json.dumps(fallback, ensure_ascii=False) + ";\n"
header += "const HBAC_MESSAGE_PATTERNS = " + json.dumps(patterns, ensure_ascii=False) + ";\n"
header += (FRONTEND / "i18n-core.js").read_text(encoding="utf-8")
path.write_text(header + "\n/* END GENERATED I18N */\n" + source, encoding="utf-8")
print(f"Embedded {len(fallback)} fallback strings and {len(patterns)} message patterns.")
