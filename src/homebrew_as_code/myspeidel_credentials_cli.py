"""Explicit MySpeidel Windows Credential Manager setup/status/clear CLI."""
from __future__ import annotations

import argparse
import getpass
import sys

from .myspeidel_credentials import (
    CredentialStoreError, clear_credentials, load_credentials, save_credentials,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Windows Credential Manager for MySpeidel')
    parser.add_argument('action', choices=('setup', 'status', 'clear'))
    args = parser.parse_args(argv)
    try:
        if args.action == 'status':
            print('MySpeidel credential: ' + ('configured' if load_credentials() else 'not configured'))
        elif args.action == 'setup':
            username = input('MySpeidel username: ').strip()
            password = getpass.getpass('MySpeidel password (hidden): ')
            if input('Save credentials in Windows Credential Manager? [yes/NO]: ').strip() != 'yes':
                print('Cancelled; no credentials stored.')
                return 0
            save_credentials(username, password)
            print('MySpeidel credential stored in Windows Credential Manager.')
        else:
            if input('Delete the stored MySpeidel credential? [yes/NO]: ').strip() != 'yes':
                print('Cancelled.')
                return 0
            clear_credentials()
            print('MySpeidel credential cleared (if previously present).')
        return 0
    except (CredentialStoreError, OSError, EOFError, KeyboardInterrupt, ValueError):
        print('Credential Manager operation failed; no secret details displayed.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
