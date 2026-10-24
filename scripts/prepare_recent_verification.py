"""Materialize per-problem verification probes from saved original statements."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'docs/contests/20261024/abc481'
EVIDENCE = ROOT / '.backups/recent-20261024'


def main():
    samples = []
    (STAGE / '_work/logs').mkdir(parents=True, exist_ok=True)
    for letter in 'ABCDEF':
        source = json.loads((EVIDENCE / 'statements' / f'remote_atcoder_abc481__{letter}.json').read_text(encoding='utf-8'))
        for i, item in enumerate(source['samples'], 1):
            samples.append((f'{letter} sample {i}', item['input'], item['output']))
        p = STAGE / 'A-F' / letter
        rounds = 1500 if letter == 'E' else 500 if letter in 'DF' else 300
        text = f'''from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
CONTEST = HERE.parents[1]
sys.path.insert(0, str(CONTEST))
import cases
sys.path.insert(0, str(Path.home()/'.dsh/tools'))
from verify import main
def gen(rng): return cases.gen('{letter}', rng)
EDGES = cases.EDGES['{letter}']
LIMITS = [('题面最大规模', lambda: cases.full('{letter}'), {source['limits']['timeMs'] / 1000})]
if __name__ == '__main__':
    main(solution=str(HERE/'{letter.lower()}.cpp'), brute=str(HERE/'{letter.lower()}_brute.cpp'), gen=gen,
         edges=EDGES, limits=LIMITS, rounds={rounds}, seed=20261024, letter='{letter}',
         samples_file=str(CONTEST/'_work/samples.py'), log_file=str(CONTEST/'_work/logs/verify_{letter}.log'))
'''
        (p / f'verify_{letter.lower()}.py').write_text(text, encoding='utf-8')
    (STAGE / '_work/samples.py').write_text('SAMPLES = ' + repr(samples) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
