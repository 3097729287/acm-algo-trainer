"""Compare actual Rust RPC list writes with the legacy service in isolated journals."""
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import argparse, hashlib, json, os, sqlite3, sys, tempfile, threading, uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common'), str(ROOT / 'scripts')]
os.environ['TB_OFFLINE'] = '1'
from custom_training_lists import add_problems, read_lists, save_list
from native_run_parity import Native
from training import ServiceError

NOW = datetime(2026, 11, 9, 17, tzinfo=timezone.utc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with closing(sqlite3.connect((ROOT / 'data/native-catalog.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)) as db:
        rows = [json.loads(row[0]) for row in db.execute('SELECT compact FROM catalogue ORDER BY position')]
        aliases = dict(db.execute('SELECT id,canonical FROM aliases'))
    by_id = {row['id']: row for row in rows}
    for alias, canonical in aliases.items():
        if alias != canonical and canonical in by_id:
            by_id[canonical].setdefault('aliasIds', []).append(alias)
    selected = [row['id'] for row in rows if not row.get('catalogHidden')][:3]
    assert len(selected) == 3
    alias = next((key for key, value in aliases.items() if value == selected[0] and key != value), selected[0])
    checks = []
    with tempfile.TemporaryDirectory(prefix='ToBe-native-custom-lists-') as folder:
        folder = Path(folder); reference_db = folder / 'legacy.sqlite3'
        with closing(sqlite3.connect(reference_db)) as db:
            db.execute('CREATE TABLE account_preferences(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL)')
            reference = SimpleNamespace(connection=db, db_path=reference_db, lock=threading.RLock(), _now=lambda: NOW,
                                        _library=lambda: rows, _write=lambda: db)
            def row(identity):
                value = by_id.get(aliases.get(identity, identity))
                if value is None:raise ServiceError(404, '没有找到这道题')
                return value
            reference._row = row
            native = Native(args.native, folder / 'native', Path('D:/Work/Msys64/ucrt64/bin/g++.exe'), Path(sys.executable), test_clock=NOW.isoformat())
            try:
                capabilities = native.call('api/capabilities')
                assert capabilities['legacyImplemented'] == 36 and capabilities['legacyTotal'] == 136
                def compare(path, body):
                    actual = native.call(path, body)
                    if path.endswith('/save') and not body.get('id'):
                        generated = uuid.UUID(actual['list']['id'].removeprefix('custom:'))
                        with patch('custom_training_lists.uuid.uuid4', return_value=generated):expected = save_list(reference, body)
                    else:expected = save_list(reference, body) if path.endswith('/save') else add_problems(reference, body)
                    assert actual == expected, path
                    checks.append(path)
                    return actual
                first = compare('training-lists/save', {'title':'我的题单 🦀','problemIds':[selected[0], alias, selected[0]]})['list']
                second = compare('training-lists/save', {'title':'周末复习'})['list']
                compare('training-lists/add', {'listIds':[first['id'], second['id'], first['id']], 'problemIds':[alias, *selected]})
                compare('training-lists/add', {'listIds':[first['id'], second['id']], 'problemIds':selected})
                compare('training-lists/save', {'id':first['id'], 'title':'重排','problemIds':list(reversed(selected))})
                compare('training-lists/save', {'id':second['id'], 'deleted':True})
                assert native.call('training-lists', query={'custom':'1'}) == {'lists':read_lists(reference)}
                with closing(sqlite3.connect(folder / 'native/personal.sqlite3')) as saved:
                    a=[(k,json.loads(v),at) for k,v,at in saved.execute("SELECT * FROM account_preferences WHERE key LIKE 'custom-training-list:%' OR key LIKE 'activity-actions:%' ORDER BY key")]
                    b=[(k,json.loads(v),at) for k,v,at in db.execute('SELECT * FROM account_preferences ORDER BY key')]
                    assert a == b
                    assert saved.execute('SELECT count(*) FROM submissions').fetchone()[0] == 0
                checks.append('same-durable-documents-and-real-actions')
                native.close()
                native=Native(args.native, folder/'native', Path('D:/Work/Msys64/ucrt64/bin/g++.exe'), Path(sys.executable), test_clock=NOW.isoformat())
                assert native.call('training-lists',query={'custom':'1'}) == {'lists':read_lists(reference)}
                checks.append('actual-native-process-restart')
            finally:native.close()
    report={'ok':True,'checks':checks,'sourceBaseVersion':'1.6.8','publicCatalogueRows':len(rows),'nativeEndpoints':capabilities['legacyImplemented'],'legacyEndpoints':capabilities['legacyTotal'],'releaseReady':capabilities['releaseReady'],'realRustRpc':True,'legacyBackendUsedInsideRust':False,'officialAcClaims':0,'personalDataUsed':False,'nativeBinarySha256':hashlib.sha256(args.native.read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':main()
