"""Bundle the same tested OJ adapters for Edge/Chrome, without remote code."""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'desktop'))
sys.path.insert(0, str(ROOT / 'backend'))
from browser_extension_bundle import build


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    parser.add_argument('--base-url', default='http://127.0.0.1:18765')
    args=parser.parse_args()
    print(build(args.destination,args.base_url))
