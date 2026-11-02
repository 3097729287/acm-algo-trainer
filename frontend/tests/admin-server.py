"""Normal application with private synthetic admin state and loopback management."""
import json
import os
from pathlib import Path
import sys
import threading
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/p) for p in ('backend','backend/common','desktop')]
from backend import create_server
from library import LibraryDatabase
from test_library import record
from test_training import Assets, Judge
from preferences import save_preferences

state=Path(os.environ['TB_STATE_DIR']).resolve()
assert state.is_relative_to((ROOT/'.backups').resolve())
assert urlsplit(sys.argv[1]).hostname=='127.0.0.1'
database=LibraryDatabase(state/'library.sqlite3')
database.import_records([record()],{}, {})
server=create_server(admin_mode=True,training_file=state/'tb-personal.sqlite3',library_file=database.path,
    data_root=state,data_file=state/'absent.md',integration_auto_start=False,assets=Assets(None),judge=Judge(),
    account_endpoint=sys.argv[1],backup_dir=state/'backups',dist_dir=Path(os.environ['TB_UI_DIST']))
server.training.save_draft('fixture::A','private maintenance draft')
save_preferences(server.training,{'preferences':{'onboardingCompleted':True,'onboardingGuideVersion':2,
    'levelNoticeVersion':1,'levelNoticeSeen':100,'levelNoticePending':0}})
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
print(json.dumps({'ok':True,'baseUrl':f'http://127.0.0.1:{server.server_port}'}),flush=True)
try:sys.stdin.readline()
finally:server.shutdown();server.server_close();thread.join(3)
