"""Lower-level UI fixture. Production CLI always retains its account gate."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / path) for path in ('backend', 'backend/common', 'desktop')]
from backend import create_server

state = Path(os.environ['TB_STATE_DIR']).resolve()
if os.environ.get('TB_OFFLINE') != '1':
    raise RuntimeError('This fixture must be offline and use a disposable state directory')
server = create_server(port=0, training_file=state / 'tb-personal.sqlite3', library_file=state / 'tb-library.sqlite3',
                       require_account=False, integration_auto_start=False)
print(f'TB test API http://127.0.0.1:{server.server_port}', flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
