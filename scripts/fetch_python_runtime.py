"""Fetch the pinned official CPython embeddable runtime for offline distribution."""
import argparse
import hashlib
import io
from pathlib import Path
from urllib.request import urlopen
import zipfile

VERSION='3.13.16'
URL=f'https://www.python.org/ftp/python/{VERSION}/python-{VERSION}-embed-amd64.zip'
SHA256='97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297'

def fetch(destination):
    destination=Path(destination).resolve()
    if destination.exists():
        raise ValueError('Choose an empty runtime destination')
    with urlopen(URL,timeout=60) as response:
        data=response.read(32*1024*1024)
    if hashlib.sha256(data).hexdigest()!=SHA256:
        raise ValueError('Official CPython archive checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            path=destination/item.filename
            if not path.resolve().is_relative_to(destination):
                raise ValueError('Invalid runtime archive path')
        archive.extractall(destination)
    if not (destination/'python.exe').is_file() or not (destination/'LICENSE.txt').is_file():
        raise ValueError('Incomplete CPython archive')
    print(f'Verified CPython {VERSION}: {SHA256}')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('destination',type=Path)
    fetch(parser.parse_args().destination)
