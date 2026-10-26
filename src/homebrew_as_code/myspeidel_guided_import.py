"""Guided, resumable MySpeidel import; reuses the 0020q-t validators/transports."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4

from .brew_plan import load_brew_plan
from .myspeidel_import_builder import KINDS, make_template, build_import_draft
from .myspeidel_create_candidate import policy_from_backup, build_candidate
from .myspeidel_create_dry_run import read_json, validate
from .myspeidel_live_create import verify_receipt
from .myspeidel_put_roundtrip import digest, read_backup, write_new

ROOT = Path('.local/myspeidel-imports')
REGISTRY = Path('.local/myspeidel-ingredient-mapping.json')
FORMAT = 'homebrew-as-code/myspeidel-guided-import-v1'
MAP_FORMAT = 'homebrew-as-code/myspeidel-ingredient-mapping-v1'


def display(value):
    return json.dumps(str(value), ensure_ascii=True)


def choose(label, rows, input_fn=input, output_fn=print):
    if not rows:
        raise ValueError(label + ': no available entries')
    output_fn(label)
    for index, (name, _) in enumerate(rows, 1):
        output_fn(f'  {index}  {display(name)}')
    answer = input_fn('Select number (Enter cancels): ').strip()
    if not answer:
        raise ValueError('Cancelled; no action selected')
    if not answer.isascii() or not answer.isdecimal() or not 1 <= int(answer) <= len(rows):
        raise ValueError('Invalid selection')
    return rows[int(answer)-1][1]


def local(path):
    path = Path(path).resolve()
    if not path.is_relative_to(Path('.local').resolve()):
        raise ValueError('Expected a path under project .local')
    return path


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    try:
        with temp.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, ensure_ascii=True, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        stream = path.open('x', encoding='utf-8')
    except FileExistsError:
        raise ValueError(f'Workflow lock exists: {path}. Check for another process before removing a stale lock.') from None
    try:
        with stream:
            stream.write(str(os.getpid())); stream.flush()
        yield
    finally:
        path.unlink(missing_ok=True)


def needed(recipe, settings):
    names = {k: [] for k in KINDS}
    names['water_types'] = [settings['water_name']]
    names['malts'] = [x['name'] for x in recipe['fermentables']]
    names['yeasts'] = [recipe['yeast']['name']]
    for item in recipe['boil']['additions']:
        names['hops' if 'alpha_acid_percent' in item else 'ingredients'].append(item['ingredient'])
    return {k: list(dict.fromkeys(v)) for k,v in names.items()}


def normal(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Ingredient name must be non-empty text')
    return ' '.join(name.casefold().split())


def resolve_mapping(recipe, settings, source, registry, input_fn=input, output_fn=print):
    """Account/category scoped exact matches or explicit aliases; never invent IDs."""
    if registry.get('format') != MAP_FORMAT:
        raise ValueError('Unexpected mapping registry format')
    catalog = make_template(source)['references']
    for kind in KINDS:
        catalog[kind] = [x for x in catalog[kind] if source['references'][kind][x['uuid']].get('deleted', 0) == 0]
    updated = deepcopy(registry)
    account = source['owner']['uuid']
    mappings = updated.setdefault('accounts', {}).setdefault(account, {})
    template = {'format': 'homebrew-as-code/myspeidel-import-template-v1',
                'references': {k: [] for k in KINDS}}
    decisions = []
    for kind, names in needed(recipe, settings).items():
        for name in names:
            key = normal(name)
            saved = mappings.get(kind, {}).get(key)
            valid = [x for x in catalog[kind] if saved and x['uuid'] == saved.get('uuid')
                     and x['name'] == saved.get('name')]
            origin = 'saved'
            if len(valid) == 1:
                selected = valid[0]
            else:
                exact = [x for x in catalog[kind] if normal(x['name']) == key]
                if len(exact) == 1 and saved is None:
                    selected = exact[0]; origin = 'exact_name'
                else:
                    if saved:
                        output_fn('Saved mapping is unavailable or renamed; select again: ' + display(name))
                    rows = sorted(catalog[kind], key=lambda x: (normal(x['name']) != key, normal(x['name']), x['uuid']))
                    selected = choose(f'{kind}: {name}', [(x['name']+' ['+x['uuid']+']',x) for x in rows], input_fn, output_fn)
                    origin = 'explicit_selection'
            mappings.setdefault(kind, {})[key] = dict(selected)
            # Canonical name is an adapter alias, not a rename of the remote catalog.
            template['references'][kind].append({'uuid':selected['uuid'], 'name':name})
            decisions.append({'category':kind,'recipe_name':name,'catalog_name':selected['name'],
                              'uuid':selected['uuid'],'selection':origin})
    return template, updated, decisions


def draft_with_mapping(loaded, settings, source, template, decisions, spec):
    candidate, report = build_import_draft(loaded['recipe'],template,settings,spec=spec)
    for kind in KINDS:
        for uid, obj in candidate['references'][kind].items():
            obj['name'] = source['references'][kind][uid]['name']
    report['candidate_sha256'] = digest(candidate)
    report['ingredient_mapping'] = decisions
    report['brew_plan_warnings'] = loaded['warnings']
    report['equipment_id'] = loaded['equipment']['equipment']['id']
    report['blockers'].append('Equipment is not automatically converted or scaled; review policy machine_type.')
    return {'format':'homebrew-as-code/myspeidel-import-draft-v1','candidate':candidate,'report':report}


def plans(repo):
    rows = []
    for path in sorted((repo/'brew-plans').glob('*.yaml')):
        try:
            data = load_brew_plan(path,repo_root=repo)
            label = f"{data['recipe']['recipe']['name']} | {data['plan']['brew_plan']['id']} | {data['equipment']['equipment']['model']}"
            rows.append((label,(path,data)))
        except ValueError as exc:
            print('Skipped invalid plan:',path.name, str(exc))
    return rows


def start(args):
    repo = Path.cwd()
    if args.plan:
        plan = Path(args.plan).resolve()
        loaded = load_brew_plan(plan,repo_root=repo)
    else:
        plan, loaded = choose('Select recipe / brew plan', plans(repo))
    if args.backup:
        backup = local(args.backup)
    else:
        rows = []
        for path in sorted(Path('.local').glob('*.json')):
            try:
                _, recipe, _ = read_backup(path)
                rows.append((recipe['name']+' | '+path.name,path))
            except (ValueError,OSError,KeyError,TypeError):
                continue
        backup = choose('Select source GET backup (catalog/account/equipment)',rows)
    _, source, _ = read_backup(backup)
    make_template(source)  # Validate catalog IDs/names before creating a session.
    settings = read_json(Path(args.settings))
    spec = read_json(local(args.spec))
    ident = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')+'-'+uuid4().hex[:8]
    folder = local(ROOT/ident); folder.mkdir(parents=True)
    snapshots = {'backup.json':read_json(backup),'spec.json':spec,'plan-snapshot.json':loaded}
    for name,value in snapshots.items():write_new(folder/name,value)
    write_new(folder/'settings.json',settings)
    write_new(folder/'policy.json',policy_from_backup(source))
    state = {'format':FORMAT,'id':ident,'label':loaded['recipe']['recipe']['name'],
             'plan_path':str(plan),'fixed':{k:digest(v) for k,v in snapshots.items()},'frozen':{},
             'dry_runs':[],'live_runs':[]}
    write_new(folder/'session.json',state)
    print('Session:',folder)
    print('Review settings:',folder/'settings.json')
    print('Review recipe/account/equipment policy:',folder/'policy.json')
    print('Set policy assumptions_accepted=true after review, then resume. No HTTP.')
    return folder


def read_session(folder):
    folder = local(folder)
    s = read_json(folder/'session.json')
    if s.get('format') != FORMAT:
        raise ValueError('Unexpected session format')
    for name, sha in {**s['fixed'], **s['frozen']}.items():
        if Path(name).name != name or digest(read_json(folder/name)) != sha:
            raise ValueError('Session input changed: '+name)
    return s


def candidate_artifact(folder, state):
    # Recover a candidate written just before a process interruption; never regenerate IDs.
    if (folder/'candidate.json').exists():
        if not state['frozen']:
            inputs = read_json(folder/'prepared-inputs.json')
            for name, sha in inputs.items():
                if Path(name).name != name or digest(read_json(folder/name)) != sha:
                    raise ValueError('Prepared input changed during interrupted preparation')
            state['frozen'] = {**inputs,'candidate.json':digest(read_json(folder/'candidate.json'))}
            atomic_json(folder/'session.json',state)
        return read_json(folder/'candidate.json')
    return None


def prepare(folder, state):
    if candidate_artifact(folder,state):
        raise ValueError('Candidate already exists; resume it instead of rebuilding IDs')
    loaded=read_json(folder/'plan-snapshot.json');settings=read_json(folder/'settings.json')
    policy=read_json(folder/'policy.json');spec=read_json(folder/'spec.json')
    _,source,_=read_backup(folder/'backup.json')
    if loaded['recipe'].get('schema_version') == 2:
        from .recipe_completeness import assess
        status = assess(loaded['recipe'], settings)
        if status['myspeidel_mapping_blockers']:
            raise ValueError('MySpeidel mapping needs: ' + '; '.join(status['myspeidel_mapping_blockers']))
    if policy.get('assumptions_accepted') is not True:
        raise ValueError('Review policy.json and set assumptions_accepted=true first')
    registry_path = local(REGISTRY)
    with locked(registry_path.with_suffix('.lock')):
        registry = read_json(registry_path) if registry_path.exists() else {'format':MAP_FORMAT,'accounts':{}}
        template, updated, decisions = resolve_mapping(loaded['recipe'],settings,source,registry)
        for row in decisions:
            print(display(row['recipe_name']), '->', display(row['catalog_name']), row['uuid'], '['+row['selection']+']')
        if input('Confirm these ingredient mappings? [yes/NO]: ').strip() != 'yes':
            print('Cancelled; mapping registry and candidate unchanged.');return
        draft = draft_with_mapping(loaded,settings,source,template,decisions,spec)
        artifact = build_candidate(draft,source,policy,spec)
        validate(artifact,source,spec)
        # Persist snapshots before candidate. Partial preparation can be safely resumed.
        for name,value in [('template.json',template),('draft.json',draft),('mapping.json',decisions)]:
            atomic_json(folder/name,value)
        frozen={name:digest(read_json(folder/name)) for name in
                ('settings.json','policy.json','template.json','draft.json','mapping.json')}
        atomic_json(folder/'prepared-inputs.json',frozen)
        atomic_json(registry_path,updated)
        write_new(folder/'candidate.json',artifact)
        state['frozen']={**frozen,'candidate.json':digest(artifact)}
        atomic_json(folder/'session.json',state)
    print('Prepared candidate:',artifact['candidate']['uuid'])
    print('Mappings saved. Next: resume for dry-run. No HTTP performed.')


def latest_receipt(folder,state,candidate,source):
    for name in reversed(state['dry_runs']):
        if Path(name).name != name:raise ValueError('Invalid report filename')
        try:
            report=read_json(folder/name)
            verify_receipt(report,candidate,source)
            return folder/name
        except (ValueError,KeyError,TypeError,OSError):pass
    return None


def actions(folder,state):
    artifact=candidate_artifact(folder,state)
    if not artifact:return [('Prepare candidate (offline)','prepare')]
    _,source,_=read_backup(folder/'backup.json')
    candidate,_=validate(artifact,source,read_json(folder/'spec.json'))
    receipt=latest_receipt(folder,state,candidate,source)
    marker=Path('.local/myspeidel-create-attempts')/(candidate['uuid']+'.json')
    # Once live mode was entered, never offer another create even after hard interruption.
    if state['live_runs'] or marker.exists():
        return [('Verify saved recipe (GET only)','verify')] if receipt else []
    if receipt:
        return [('Create new private recipe (REAL POST)','create'),('Run another dry-run','dry')]
    return [('Run POST dry-run and GET checks','dry')]


def perform(folder,state,action):
    if action=='prepare':prepare(folder,state);return 0
    from .myspeidel_create_dry_run import main as dry_main
    from .myspeidel_live_create import main as live_main
    is_dry=action=='dry'
    key='dry_runs' if is_dry else 'live_runs'
    filename=('dry-' if is_dry else 'live-')+uuid4().hex+'.json'
    state[key].append(filename)
    # Record intent before calling a child CLI; retain after failure/interruption.
    atomic_json(folder/'session.json',state)
    argv=['--candidate',str(folder/'candidate.json'),'--backup',str(folder/'backup.json'),
          '--spec',str(folder/'spec.json'),'--diagnostics',str(folder/filename)]
    if not is_dry:
        _,source,_=read_backup(folder/'backup.json')
        receipt=latest_receipt(folder,state,read_json(folder/'candidate.json')['candidate'],source)
        if receipt is None:raise ValueError('No matching successful dry-run report')
        argv += ['--receipt',str(receipt)]
        if action=='verify':argv.append('--verify-only')
    result=(dry_main if is_dry else live_main)(argv)
    if not is_dry and not (folder/filename).exists():
        # Child returned before reserving diagnostics, hence before any HTTP.
        state[key].remove(filename)
        atomic_json(folder/'session.json',state)
    print('Step exit code:',result,'Report:',folder/filename)
    print('Resume this session to see the next available step.')
    return result


def select_session(value):
    if value:return local(value)
    rows=[]
    for path in sorted(ROOT.glob('*/session.json')):
        try:
            s=read_json(path)
            rows.append((s['label']+' | '+s['id'],path.parent))
        except (ValueError,OSError,KeyError,TypeError):continue
    return choose('Select import session',rows)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    init=sub.add_parser('start')
    init.add_argument('--plan');init.add_argument('--backup')
    init.add_argument('--settings',default='examples/myspeidel-import-settings.json')
    init.add_argument('--spec',default='.local/vendor/myspeidel-openapi.json')
    for name in ('resume','status'):
        p=sub.add_parser(name);p.add_argument('--session')
    args=parser.parse_args(argv)
    try:
        if args.command=='start':start(args);return 0
        folder=select_session(args.session)
        with locked(folder/'.workflow.lock'):
            state=read_session(folder)
            print('Import:',display(state['label']),state['id'])
            available=actions(folder,state)
            for name in state['dry_runs']+state['live_runs']:
                if Path(name).name!=name:raise ValueError('Invalid report filename')
                if (folder/name).exists():
                    report=read_json(folder/name)
                    print(name,report.get('result',report.get('status','unknown')))
                else:print(name,'No report; cancelled or interrupted before report creation')
            print('Next:',', '.join(label for label,_ in available) or 'Inspect evidence manually')
            if args.command=='resume':return perform(folder,state,choose('Choose next step',available))
        return 0
    except (ValueError,OSError,KeyError,TypeError,EOFError,KeyboardInterrupt) as exc:
        print('Workflow stopped:',str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
