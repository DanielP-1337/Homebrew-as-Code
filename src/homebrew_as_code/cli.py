"""Command-line entry point for recipe checks."""

import argparse
import sys

from .recipe import RecipeError, load_recipe
from .water import mineral_profile, split_salts


def main() -> int:
    parser = argparse.ArgumentParser(description="Homebrew-as-Code validation")
    parser.add_argument("command", choices=["validate", "water"])
    parser.add_argument("path", help="Path to recipe.yaml")
    args = parser.parse_args()
    try:
        recipe = load_recipe(args.path)
        if args.command == "validate":
            print(f"PASS: {recipe['recipe']['name']} v{recipe['recipe']['version']}")
            return 0
        water = recipe["water"]
        salts = water["salts_g"]
        volume = water["total_l"]
        profile = mineral_profile(volume, salts["calcium_chloride_dihydrate"], salts["calcium_sulfate_dihydrate"])
        print("Added ions (RO baseline excluded):")
        print(f"  Ca:  {profile.calcium_mg_l:.1f} mg/L")
        print(f"  Cl:  {profile.chloride_mg_l:.1f} mg/L")
        print(f"  SO4: {profile.sulfate_mg_l:.1f} mg/L")
        for salt, amount in salts.items():
            mash, sparge = split_salts(amount, water["mash_l"], water["sparge_l"])
            print(f"  {salt}: mash {mash:.2f} g / sparge {sparge:.2f} g")
        return 0
    except RecipeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
