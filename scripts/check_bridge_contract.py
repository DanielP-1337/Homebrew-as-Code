"""Check generated payloads against the actual PR #30 Bridge encoder (no I/O)."""
import importlib.util
import sys
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


root = Path(__file__).resolve().parents[1]
converter = load("converter", root / "custom_components/hbac/converter.py")
bridge = load("bridge_contract", Path(sys.argv[1]))
source = {"name": "Märzen Rezept", "boilTime": 60,
          "mash": {"steps": [{"stepTemp": 63, "stepTime": 40}, {"stepTemp": 78, "stepTime": 10}]},
          "hops": [{"name": "A", "use": "Boil", "time": 60}, {"name": "B", "use": "Boil", "time": 15}]}
program = converter.convert(source, "recipes", "synthetic")["program"]
for fahrenheit in (False, True):
    for slot in range(1, 10):
        line = bridge.recipe_line(slot, program, fahrenheit)
        assert line.endswith(".Maerzen Rezept")
        numbers = line.split(".")[0].split("X")
        assert len(numbers) == 20
        assert int(numbers[0]) == slot
        assert int(numbers[1]) == (145 if fahrenheit else 63)
print("18 PR #30 encoder checks passed: all nine slots in Celsius and Fahrenheit.")
