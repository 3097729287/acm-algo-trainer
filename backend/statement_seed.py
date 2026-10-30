"""Guarded, sharded public statement repairs on top of the existing text seed.

Only statement rows are replaced. A changed authoring baseline is a conflict,
not permission to overwrite later translations or another content session.
"""
import hashlib
import json
from pathlib import Path


def checksum(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf8')).hexdigest()


def load_statements(directory):
    directory = Path(directory)
    rows = json.loads((directory / 'statements.json').read_text('utf8'))
    by_id = {row['problem_id']: row for row in rows}
    for path in sorted((directory / 'statement-patches').glob('*.json')):
        packet = json.loads(path.read_text('utf8'))
        if packet.get('schema') != 1 or set(packet) != {'schema', 'statements'}:
            raise ValueError('Invalid public statement repair packet: ' + path.name)
        for patch in packet['statements']:
            identity, incoming = patch['problem_id'], patch['content']
            old = by_id.get(identity, {}).get('content')
            if old != incoming and checksum(old) != patch['beforeSha256']:
                raise ValueError('Statement repair conflicts with newer content: ' + identity)
            if incoming.get('id') != identity:
                raise ValueError('Statement repair changes original identity: ' + identity)
            by_id[identity] = {'problem_id': identity, 'content': incoming}
    return [by_id[identity] for identity in sorted(by_id)]
