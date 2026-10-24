"""Opt-in Windows Credential Manager support for MySpeidel account credentials.

Uses Windows Credential Manager Generic credentials scoped to the signed-in
Windows user. No filesystem password storage, tokens, or implicit enrollment.
"""
from __future__ import annotations

import ctypes
import getpass
import sys
from ctypes import wintypes

TARGET = 'Homebrew-as-Code/MySpeidel/v1'
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168


class CredentialStoreError(RuntimeError):
    """Safe credential-store error without embedded account or secret details."""


class _CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
        ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]


PCREDENTIAL = ctypes.POINTER(_CREDENTIAL)


def _api():
    if sys.platform != 'win32':
        raise CredentialStoreError('Windows Credential Manager requires Windows')
    dll = ctypes.WinDLL('Advapi32.dll', use_last_error=True)
    dll.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               ctypes.POINTER(PCREDENTIAL)]
    dll.CredReadW.restype = wintypes.BOOL
    dll.CredWriteW.argtypes = [PCREDENTIAL, wintypes.DWORD]
    dll.CredWriteW.restype = wintypes.BOOL
    dll.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    dll.CredDeleteW.restype = wintypes.BOOL
    dll.CredFree.argtypes = [ctypes.c_void_p]
    dll.CredFree.restype = None
    return dll


def load_credentials() -> tuple[str, str] | None:
    api = _api()
    pointer = PCREDENTIAL()
    if not api.CredReadW(TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        if ctypes.get_last_error() == ERROR_NOT_FOUND:
            return None
        raise CredentialStoreError('Credential read failed')
    try:
        credential = pointer.contents
        length = credential.CredentialBlobSize
        if not 0 < length <= 5120 or length % 2:
            raise CredentialStoreError('Invalid stored credential data')
        blob = ctypes.string_at(credential.CredentialBlob, length)
        password = blob.decode('utf-16-le')
        username = credential.UserName
        if not username or not password:
            raise CredentialStoreError('Stored credential is incomplete')
        return username, password
    finally:
        api.CredFree(pointer)


def save_credentials(username: str, password: str) -> None:
    if not username or not username.strip() or not password:
        raise CredentialStoreError('Username and password are required')
    api = _api()
    encoded = password.encode('utf-16-le')
    if len(encoded) > 5120:
        raise CredentialStoreError('Password exceeds Windows credential size limit')
    buf = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
    credential = _CREDENTIAL()
    credential.Type = CRED_TYPE_GENERIC
    credential.TargetName = TARGET
    credential.UserName = username.strip()
    credential.CredentialBlobSize = len(encoded)
    credential.CredentialBlob = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))
    credential.Persist = CRED_PERSIST_LOCAL_MACHINE
    if not api.CredWriteW(ctypes.byref(credential), 0):
        raise CredentialStoreError('Credential write failed')


def clear_credentials() -> bool:
    api = _api()
    if api.CredDeleteW(TARGET, CRED_TYPE_GENERIC, 0):
        return True
    if ctypes.get_last_error() == ERROR_NOT_FOUND:
        return False
    raise CredentialStoreError('Credential deletion failed')


def prompt_credentials() -> tuple[str, str]:
    """Prefer opt-in vault; otherwise use the original interactive prompts."""
    saved = load_credentials()
    if saved is not None:
        return saved
    return input('MySpeidel username: ').strip(), getpass.getpass('MySpeidel password: ')
