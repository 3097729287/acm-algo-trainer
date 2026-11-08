"""Run the full disposable backend suite with explicit paths and no live default service."""
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
os.environ['TB_OFFLINE']='1'
sys.path[:0]=[str(ROOT),str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'desktop')]


def main():
    loader=unittest.TestLoader()
    suite=loader.discover(str(ROOT/'backend'))
    # Missing modules must be reported before a lengthy integration run, rather
    # than silently replacing whole modules with one _FailedTest placeholder.
    if loader.errors:
        for error in loader.errors:sys.stderr.write(error+'\n')
        return 2
    print(f'Loaded {suite.countTestCases()} backend checks; default remote service disabled',flush=True)
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
