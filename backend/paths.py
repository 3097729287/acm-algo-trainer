"""Paths shared by API, desktop and release builds; never depend on the cwd."""
from pathlib import Path
import os
import sys

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
RESOURCES = ROOT / 'resources' if getattr(sys, 'frozen', False) else ROOT / 'backend' / 'resources'
ADMIN_MODE = '--admin' in sys.argv or os.environ.get('TB_ADMIN_MODE') == '1' or getattr(sys,'frozen',False) and Path(sys.executable).stem=='TB管理员版'
STATE = Path(os.environ.get('TB_STATE_DIR') or (ROOT / 'admin-workspace' / 'state' if ADMIN_MODE else ROOT / 'state')).resolve()
FRONTEND = ROOT / 'frontend' / 'dist'
LIBRARY_SEED = ROOT / 'data' / 'library.sqlite3'
LIBRARY_SOURCE = ROOT / 'data' / 'library'

def resource(name):
    return RESOURCES / name
