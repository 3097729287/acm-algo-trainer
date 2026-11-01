"""Lower-level UI fixture. Production CLI always retains its account gate."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / path) for path in ('backend', 'backend/common', 'desktop')]
from backend import create_server,Handler
import traceback

original_json=Handler.send_json
def traced_json(self,status,value):
    if status==500:traceback.print_exc()
    return original_json(self,status,value)
Handler.send_json=traced_json

state = Path(os.environ['TB_STATE_DIR']).resolve()
if os.environ.get('TB_OFFLINE') != '1':
    raise RuntimeError('This fixture must be offline and use a disposable state directory')
server = create_server(port=0, training_file=state / 'tb-personal.sqlite3', library_file=state / 'tb-library.sqlite3',
                       require_account=False, integration_auto_start=False)
original_preview=server.training.preview_contest
def traced_preview(body):
    try:return original_preview(body)
    except Exception:
        import traceback
        traceback.print_exc()
        raise
server.training.preview_contest=traced_preview
print(f'TB test API http://127.0.0.1:{server.server_port}', flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
