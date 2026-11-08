"""Compile public reviewed-case identities; never execute a Python judge."""
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compile_profiles(root=ROOT, *, check=False):
    source = (root / 'backend/reviewed_cases.py').read_text(encoding='utf-8-sig').replace('\r\n', '\n')
    tree = ast.parse(source)
    profiles = next(ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'PROFILES' for target in node.targets))
    if not isinstance(profiles, dict) or not all(isinstance(key, str) and key and isinstance(value, str) for key, value in profiles.items()):
        raise ValueError('Invalid public reviewed-case identity metadata')
    result = {'version': 1, 'normalization': 'utf8-lf',
              'sourceSha256': hashlib.sha256(source.encode('utf8')).hexdigest(), 'ids': sorted(profiles)}
    content = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    destination = root / 'backend/resources/native-reviewed-profiles.json'
    if check:
        if not destination.is_file() or destination.read_text('utf8') != content:
            raise ValueError('Native reviewed-case metadata is stale; run scripts/native_reviewed_profiles.py')
    else:
        destination.write_text(content, encoding='utf8', newline='\n')
    return result


if __name__ == '__main__':
    result = compile_profiles(check='--check' in sys.argv)
    print(f"{len(result['ids'])} public reviewed-case identities {'checked' if '--check' in sys.argv else 'compiled'}")
