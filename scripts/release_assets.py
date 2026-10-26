"""Validate the public upload boundary. The owner's admin edition stays local."""
import argparse
import json
from pathlib import Path
import re


def is_admin_asset(name):
    return bool(re.search(r'(^|[-_/\\])admin(?:[-_.]|$)|管理员', str(name), re.I))


def public_asset_name(name):
    if is_admin_asset(name):
        return False
    version = r'\d+\.\d+\.\d+'
    return name in {'BUILD-INFO.json', 'SOURCE-MANIFEST.json', 'RELEASE-MANIFEST.json', 'SHA256SUMS.txt'} or bool(re.fullmatch(
        rf'(?:ToBe|TB)-(?:Setup-{version}-win64\.exe|{version}-win64\.zip|Update-{version}-to-{version}-win64\.zip|Algorithm-Lab-{version}\.zip|Toolchain-Sources-{version}\.zip)', name))


def public_release_files(directory):
    """Fail before upload if private artifacts or their checksum references leaked."""
    directory = Path(directory)
    files = []
    for path in sorted(directory.iterdir()):
        if is_admin_asset(path.name):
            raise ValueError(f'Administrator artifact cannot be published: {path.name}')
        if not path.is_file():
            continue  # The assembled user directory is not an upload asset.
        if path.is_symlink() or not public_asset_name(path.name):
            raise ValueError(f'Unexpected public release asset: {path.name}')
        files.append(path)
    names = {path.name for path in files}
    for path in files:
        if path.name == 'SHA256SUMS.txt':
            for line in path.read_text(encoding='utf-8-sig').splitlines():
                if not line.strip():
                    continue
                pieces = line.split(maxsplit=1)
                if len(pieces) != 2 or not re.fullmatch(r'[0-9a-fA-F]{64}', pieces[0]):
                    raise ValueError('Malformed public checksum entry')
                name = pieces[1].lstrip('*')
                if not public_asset_name(name) or name not in names:
                    raise ValueError(f'Non-public checksum entry: {name}')
        elif path.name == 'BUILD-INFO.json':
            info = json.loads(path.read_text(encoding='utf-8-sig'))
            if info.get('edition') == 'admin' or info.get('adminMode') is True:
                raise ValueError('Administrator build metadata cannot be published')
    if not files:
        raise ValueError('No public release assets')
    return tuple(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({'publicAssets': [p.name for p in public_release_files(args.directory)]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
