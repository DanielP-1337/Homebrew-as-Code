"""Use the generic HA recipe actions; never connect to the brewer directly."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from .bridge_export import build_bridge_export
from .recipe import RecipeError, load_recipe


def call_action(url, token, action, data):
    request = Request(
        url.rstrip('/') + '/api/services/speidel_braumeister/' + action + '?return_response',
        data=json.dumps(data).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
        method='POST',
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)['service_response']


def main(argv=None):
    parser = argparse.ArgumentParser(description='Upload HBAC recipes through the generic HA interface')
    parser.add_argument('paths', nargs='*')
    parser.add_argument('--ha-url', required=True)
    parser.add_argument('--config-entry-id')
    parser.add_argument('--replace-all', action='store_true', help='Explicitly replace all device recipes')
    parser.add_argument('--job-file', default='bridge-upload-job.json', help='Save receipt for later status queries')
    parser.add_argument('--status', metavar='JOB_ID', help='Query an existing job without uploading')
    args = parser.parse_args(argv)
    token = os.environ.get('HA_TOKEN')
    if not token:
        parser.error('Set HA_TOKEN in the environment')
    selection = {'config_entry_id': args.config_entry_id} if args.config_entry_id else {}

    def call(action, data):
        return call_action(args.ha_url, token, action, {**selection, **data})

    try:
        if args.status:
            print(json.dumps(call('recipe_upload_status', {'job_id': args.status}), indent=2))
            return 0
        document, report = build_bridge_export([load_recipe(p) for p in args.paths])
        print(json.dumps(report, ensure_ascii=False, indent=2))
        ready = call('recipe_upload_readiness', {})
        print(json.dumps(ready, indent=2))
        if not ready['ready_for_upload']:
            raise RecipeError('Device is not ready for upload')
        if not args.replace_all:
            print('Check only. Use --replace-all to replace every device recipe.')
            return 0
        # Only one POST. A lost response must never cause automatic resubmission.
        job = call('start_recipe_upload', document)
        print('Upload job: ' + job['job_id'], flush=True)
        Path(args.job_file).write_text(json.dumps(job, indent=2) + '\n', encoding='utf-8')
        deadline = time.monotonic() + 180
        while job['result'] in ('queued', 'sending') and time.monotonic() < deadline:
            time.sleep(2)
            job = call('recipe_upload_status', {'job_id': job['job_id']})
        print(json.dumps(job, indent=2))
        if job['result'] != 'confirmed' or job.get('content_verification') == 'mismatch':
            raise RecipeError('Upload not confirmed or readback mismatch; inspect device before retrying')
        print('Device recipe count confirmed. Content readback: ' + job.get('content_verification', 'not_available'))
        return 0
    except (RecipeError, OSError, URLError, ValueError, KeyError) as exc:
        print(f'ERROR: {exc}. Do not retry uploads automatically; query the saved job ID first.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
