import json
import pytest

from homebrew_as_code.myspeidel_put_roundtrip import (
    check_private, digest, private_file, put_recipe, read_backup, write_new)

UUID = '123e4567-e89b-12d3-a456-426614174000'


def sample():
    return {'uuid': UUID, 'public': 0, 'machine_type': {'size': 20}, 'name': 'PRIVATE TEST'}


def test_private_identity_and_machine_size():
    check_private(sample(), UUID)
    for mutation in ({'public': 1}, {'uuid': 'not-the-id'}, {'machine_type': {'size': 10}}):
        changed = sample()
        changed.update(mutation)
        with pytest.raises(ValueError):
            check_private(changed, UUID)


def test_sha256_canonical_order():
    assert digest(sample()) == digest(dict(reversed(list(sample().items()))))


def test_backup_integrity(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = private_file('.local/backup.json')
    rec = sample()
    write_new(path, {'format': 'homebrew-as-code/myspeidel-put-backup-v1',
                     'uuid': UUID, 'recipe': rec, 'sha256': digest(rec)})
    assert read_backup(path)[2] == digest(rec)
    with pytest.raises(ValueError):
        private_file('.local/backup.json')
    with pytest.raises(ValueError):
        private_file('not-private.json')
    raw = json.loads(path.read_text())
    raw['recipe']['name'] = 'CHANGED'
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        read_backup(path)


def test_put_transport_is_explicit_and_narrow():
    calls = []
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, limit): return b'{"message":"DRY RUN SUCCEEDED"}'
    def opener(req, timeout):
        calls.append((req.get_method(), req.full_url, json.loads(req.data), req.get_header('Authorization')))
        return Response()
    rec = sample()
    assert put_recipe('fake-token', UUID, rec, dry_run=True, opener=opener) == 200
    assert calls[0][0] == 'PUT'
    assert calls[0][1].endswith('/' + UUID + '?dryRun=1')
    assert calls[0][2] == rec
    assert calls[0][3] == 'Bearer fake-token'
    with pytest.raises(ValueError):
        put_recipe('fake-token', UUID, rec, dry_run=1, opener=opener)
    with pytest.raises(ValueError):
        put_recipe('fake-token', UUID, {**rec, 'public': 1}, dry_run=False, opener=opener)
    assert len(calls) == 1
