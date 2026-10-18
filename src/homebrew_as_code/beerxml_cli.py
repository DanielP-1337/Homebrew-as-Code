"""BeerXML 1.0 offline export; explicitly never sends data to MySpeidel."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .beerxml_export import BeerXmlError, build_beerxml
from .recipe import RecipeError, load_recipe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build offline BeerXML 1.0 draft or manually reviewed import candidate")
    parser.add_argument("recipe", nargs="?", default="recipes/lebkuchen-zauber/recipe.yaml")
    parser.add_argument("--output", required=True, help="Destination .xml file; no overwrite")
    parser.add_argument("--parameters", help="LOCAL YAML containing measured/confirmed values (do not publish)")
    args = parser.parse_args(argv)
    try:
        target = Path(args.output)
        if target.suffix.lower() != ".xml":
            raise BeerXmlError("Output extension must be .xml")
        report = target.with_suffix(".report.json")
        if target.exists() or report.exists():
            raise BeerXmlError("Output or report already exists; refusing to overwrite")
        params = None
        if args.parameters:
            params = yaml.safe_load(Path(args.parameters).read_text(encoding="utf-8"))
            if not isinstance(params, dict):
                raise BeerXmlError("Parameters must be a YAML mapping")
        content, evidence = build_beerxml(load_recipe(args.recipe), params)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        report.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        label = "IMPORT CANDIDATE (manual review required)" if evidence["import_candidate"] else "INCOMPLETE DRAFT (do not import)"
        print(f"{label}: {target}")
        print(f"Review blockers/losses: {report}")
        return 0
    except (BeerXmlError, RecipeError, OSError, ValueError, yaml.YAMLError):
        print("ERROR: BeerXML export failed; check inputs and existing files", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
