"""Measure startup/content with isolated state; never use the user's workspace."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, help='Optional backed-up backend module directory')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    os.environ['TB_OFFLINE'] = '1'
    sys.path[:0] = [str(ROOT / p) for p in ('backend', 'backend/common', 'desktop')]
    if args.baseline:
        sys.path.insert(0, str(args.baseline.resolve()))
    from backend import create_server
    report = {}
    with tempfile.TemporaryDirectory(prefix='tb-loading-bench-') as directory:
        state = Path(directory)
        os.environ['TB_STATE_DIR'] = str(state)
        for run in ('first', 'restart'):
            start = time.perf_counter()
            server = create_server(training_file=state / 'tb-personal.sqlite3', require_account=False,
                                   integration_auto_start=False, backup_dir=state / 'backups')
            report[run] = {'serverStartMs': round((time.perf_counter() - start) * 1000, 2)}
            try:
                def measure(name, call, count=1):
                    values = []
                    for _ in range(count):
                        start = time.perf_counter()
                        call()
                        values.append((time.perf_counter() - start) * 1000)
                    report[run][name] = round(statistics.median(values), 2)
                measure('catalogFirstMs', server.store.data)
                report['problemCount'] = len(server.store.data()['rows'])
                measure('catalogRepeatMs', server.store.data, 3)
                measure('workspaceMs', server.training.workspace, 3)
                measure('statementMs', lambda: server.training.problem('ABC 478::C'), 3)
                measure('solutionFirstMs', lambda: (server.store.solution('ABC 478::C'), server.lectures.for_problem('ABC 478::C')))
                measure('solutionRepeatMs', lambda: (server.store.solution('ABC 478::C'), server.lectures.for_problem('ABC 478::C')), 3)
            finally:
                server.server_close()
            print(json.dumps({run: report[run]}), flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
