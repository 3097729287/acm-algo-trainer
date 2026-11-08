"""Inventory the existing HTTP boundary without importing or starting services.

Build/test tool only. The native program never starts Python.
"""
from pathlib import Path
import ast
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    tree = ast.parse((ROOT / 'backend/backend.py').read_text(encoding='utf-8-sig'))
    dispatch = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_dispatch')
    writing = next(n for n in ast.walk(dispatch) if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == 'writing')
    start, end = writing.body[0].lineno, writing.body[-1].end_lineno
    endpoints = set()
    for node in ast.walk(dispatch):
        # Login/register/password are dispatched through an action dictionary,
        # rather than a literal `path == ...` branch. Keep those real POST
        # operations in the inventory without importing or executing handlers.
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str) and key.value.startswith('/api/'):
                    endpoints.add(('POST' if start <= node.lineno <= end else 'GET', key.value.removeprefix('/api/')))
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Name) or node.left.id != 'path':
            continue
        for right in node.comparators:
            values = [right] if isinstance(right, ast.Constant) else right.elts if isinstance(right, (ast.Tuple, ast.List, ast.Set)) else []
            for value in values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value.startswith('/api/'):
                    endpoints.add(('POST' if start <= node.lineno <= end else 'GET', value.value.removeprefix('/api/')))
    endpoints.update((method, prefix+'/*') for method in ('GET', 'POST') for prefix in ('pk/v1', 'team-training'))
    return sorted(endpoints)


def schema():
    tree = ast.parse((ROOT / 'backend/training.py').read_text(encoding='utf-8-sig'))
    definitions = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    definitions[target.id] = node.value.value
    text = definitions['_CORE_SCHEMA_0'] + definitions['_CORE_SCHEMA_1']
    # The legacy initializer adds these columns after creating the base schema.
    text += '\n' + '\n'.join(f'ALTER TABLE {table} ADD COLUMN {column} {kind};' for table, values in {
        'training': {'active': 'INTEGER NOT NULL DEFAULT 1', 'removed_at': 'TEXT'},
        'submissions': {'sample_run': 'INTEGER NOT NULL DEFAULT 0', 'case_results': "TEXT NOT NULL DEFAULT '[]'"},
        'contests': {'config': "TEXT NOT NULL DEFAULT '{}'", 'deleted_at': 'TEXT'},
    }.items() for column, kind in values.items()) + '\n'
    return '\n'.join(line.rstrip() for line in text.splitlines()).strip() + '\n'


def files():
    contract = {
        'version': 1,
        'source': 'backend/backend.py',
        'transport': 'Tauri invoke(api_request)',
        'endpoints': [{'method': method, 'path': path, 'operation': method.lower() + '.' + path.replace('/', '.')}
                      for method, path in inventory()],
    }
    return {
        ROOT / 'api/legacy-contract.json': json.dumps(contract, ensure_ascii=False, indent=2) + '\n',
        ROOT / 'backend-rust/schema/personal.sql': schema(),
    }


if __name__ == '__main__':
    check = '--check' in sys.argv
    for path, content in files().items():
        if check:
            if not path.is_file() or path.read_text(encoding='utf-8') != content:
                raise SystemExit(f'Generated native contract is stale: {path.relative_to(ROOT)}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    from native_reviewed_profiles import compile_profiles
    compile_profiles(ROOT, check=check)
    print(f'{len(inventory())} legacy method/path pairs; contract, schema and reviewed profiles {"checked" if check else "generated"}')
