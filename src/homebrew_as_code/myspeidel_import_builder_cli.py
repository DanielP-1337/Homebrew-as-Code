"""Local template extraction and brew-plan mapping; never performs HTTP requests."""
import argparse
import json
from pathlib import Path

from .brew_plan import load_brew_plan
from .myspeidel_import_builder import make_template, build_import_draft
from .myspeidel_put_roundtrip import private_file, read_backup, write_new


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    extract = sub.add_parser('template')
    extract.add_argument('--backup', required=True)
    extract.add_argument('--output', required=True)
    build = sub.add_parser('build')
    build.add_argument('--plan', required=True)
    build.add_argument('--repo-root', default='.')
    build.add_argument('--template', required=True)
    build.add_argument('--settings', required=True)
    build.add_argument('--spec')
    build.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        output = private_file(args.output)
        if args.command == 'template':
            _, recipe, _ = read_backup(private_file(args.backup, must_exist=True))
            result = make_template(recipe)
        else:
            loaded = load_brew_plan(args.plan, repo_root=args.repo_root)
            template = json.loads(private_file(args.template, must_exist=True).read_text(encoding='utf-8'))
            settings = json.loads(Path(args.settings).read_text(encoding='utf-8'))
            spec = json.loads(Path(args.spec).read_text(encoding='utf-8')) if args.spec else None
            candidate, report = build_import_draft(loaded['recipe'], template, settings, spec=spec)
            report['brew_plan_warnings'] = loaded['warnings']
            report['equipment_id'] = loaded['equipment']['equipment']['id']
            report['blockers'].append('Equipment profile is not an API machine reference; no scaling or automatic equipment conversion.')
            result = {'format': 'homebrew-as-code/myspeidel-import-draft-v1', 'candidate': candidate, 'report': report}
        write_new(output, result)
        print('Saved local artifact. NO API requests. Import drafts are NOT upload-ready.')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
