"""Create a reproducible, credential-free HA install ZIP from explicit inputs."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.5.0-beta.3"
output = ROOT.parent / f"HBAC-{VERSION}-home-assistant.zip"
component = ROOT / "custom_components" / "hbac"
files = sorted(p for p in component.rglob("*") if p.is_file() and p.suffix in {".py", ".json", ".yaml", ".js", ".png"} and "__pycache__" not in p.parts)
files += [ROOT / "HBAC-HA.de.md", ROOT / "VALIDATION-HA.md", ROOT / "I18N.md", ROOT / "SOURCES.md", ROOT / "examples/beerxml/hbac-demo.xml", ROOT / "dashboard/hbac-test.yaml"]
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(ROOT).as_posix())
checksum = sha256(output.read_bytes()).hexdigest()
output.with_suffix(".sha256").write_text(f"{checksum}  {output.name}\n", encoding="ascii")
print(f"{output}\nSHA256: {checksum}\n{len(files)} files")
