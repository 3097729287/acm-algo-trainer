"""Disposable account UI service; never binds the normal desktop port."""
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / path) for path in ('backend', 'backend/common', 'desktop')]
from backend import create_server
from library import LibraryDatabase
from test_library import record
from test_training import Assets, Judge

state = Path(os.environ['TB_STATE_DIR']).resolve()
database = LibraryDatabase(state / 'library.sqlite3')
database.import_records([record()], {}, {})
server = create_server(training_file=state / 'tb-personal.sqlite3', library_file=database.path,
    data_root=state, data_file=state / 'absent.md', integration_auto_start=False, assets=Assets(None), judge=Judge(),
    account_endpoint=sys.argv[1], backup_dir=state / 'backups', dist_dir=ROOT / 'frontend/dist')
server.training.start_training('fixture::A')
server.training.save_draft('fixture::A', 'old private SQLite draft')
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
print(json.dumps({'ok': True, 'baseUrl': f'http://127.0.0.1:{server.server_port}', 'state': str(state)}), flush=True)
try:
    sys.stdin.readline()
finally:
    server.shutdown()
    server.server_close()
    thread.join(3)
