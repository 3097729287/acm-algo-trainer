"""Serve an isolated copy of public content for browser acceptance checks."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ('backend', 'backend/common', 'desktop')]
os.environ['TB_OFFLINE'] = '1'
parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=Path, required=True)
args = parser.parse_args()
state = ROOT / '.backups/learning-summary' / ('browser-' + str(time.time_ns()))
state.mkdir(parents=True)
seed = state / 'public.sqlite3'
shutil.copy2(args.seed, seed)
import backend
server = backend.create_server(training_file=state/'personal.sqlite3', library_file=seed,
        data_root=state, data_file=state/'absent.md', history_file=state/'history.md',
        integration_state_dir=state/'integrations', integration_auto_start=False,
        backup_dir=state/'backups', dist_dir=ROOT/'frontend/dist', admin_mode=True)
thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}', 'state': str(state)}), flush=True)
try:
    sys.stdin.readline()
finally:
    server.shutdown(); server.server_close()
