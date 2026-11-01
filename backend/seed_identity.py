"""Reuse the identity already verified by the release installer/patch manifest.

The descriptor is built with the public seed, never from a personal database.
Changed SQLite headers/sizes or missing descriptors retain the full hash path.
"""
import hashlib
import json
import re
from pathlib import Path
from paths import resource, LIBRARY_SEED

def identity(path, descriptor=None):
    path=Path(path).resolve()
    if descriptor is not None or path==LIBRARY_SEED.resolve():
        try:
            value=json.loads(Path(descriptor or resource('library-seed-identity.json')).read_text('utf8'))
            with path.open('rb') as stream:header=stream.read(100)
            if (value.get('schema')==1 and re.fullmatch('[a-f0-9]{64}',value.get('sha256',''))
                and value['bytes']==path.stat().st_size
                and value['headerSha256']==hashlib.sha256(header).hexdigest()):
                return value['sha256']
        except (OSError,ValueError,KeyError,TypeError):pass
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def describe(path):
    path=Path(path)
    with path.open('rb') as stream:
        header=stream.read(100);stream.seek(0)
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return {'schema':1,'bytes':path.stat().st_size,'sha256':digest,'headerSha256':hashlib.sha256(header).hexdigest()}
