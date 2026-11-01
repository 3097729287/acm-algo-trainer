"""Use the existing archive reconciler with a task-local Gym series adapter.

The shared tools are left unchanged; the series registration lives only in
this process, so Gym 728862 cannot be confused with a numbered CF round.
"""
from pathlib import Path
import re
import sys

TOOLS=Path.home()/'.dsh/tools'
sys.path.insert(0,str(TOOLS))
import toolutil
toolutil.SERIES['校队训练']={'dir':('Codeforces','校队训练'),'plat':'codeforces','fmt':'%s %d'}
toolutil._CONTEST_RES=(*toolutil._CONTEST_RES,(re.compile(r'^校队训练\s+(\d+)$'),'校队训练'))
import tb_sync

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8')
    raise SystemExit(tb_sync.main(['校队训练','728862',*sys.argv[1:]]))
