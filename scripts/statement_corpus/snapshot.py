"""Online backup of an explicitly named PUBLIC SQLite seed, including its WAL."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--public-seed',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
source=args.public_seed.resolve();destination=args.output.resolve()
if destination.exists() or source==destination:raise ValueError('Use a new isolated output path')
destination.parent.mkdir(parents=True,exist_ok=True)
with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src:
    tables={row[0] for row in src.execute("select name from sqlite_master where type='table'")}
    if tables.intersection({'drafts','submissions','training','accounts','documents','account_preferences'}):
        raise ValueError('This collector accepts only an explicitly supplied public seed')
    with closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
        assert dst.execute('pragma integrity_check').fetchone()[0]=='ok'
print(json.dumps({'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}))
