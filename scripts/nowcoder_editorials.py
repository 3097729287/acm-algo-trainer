"""Author, format and validate the explicitly reviewed Nowcoder training articles.

Unknown difficulty stays unknown. Candidate title/sample matches are never
imported automatically. All imports require an entry in reviewed.json and a
passing validation receipt bound to both the statement and reference program.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'data/nowcoder-editorials'
OUT = ROOT / '.backups/nowcoder-editorials'
BASELINE = ROOT.parent / 'tb-background-redesign-20261106/data/library.sqlite3'
FENCE = re.compile(r'^```(?:cpp|cxx|c\+\+)\s*\n(.*?)^```', re.M | re.S)
PY_FENCE = re.compile(r'^```(?:python|python3|py)\s*\n(.*?)^```', re.M | re.S)
os.environ.setdefault('TB_OFFLINE', '1')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def database(path=BASELINE):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def statement(identity):
    override = CONTENT / 'statements' / ('NC' + identity.split('::')[-1] + '.json')
    if identity.startswith('nowcoder-global::') and override.exists():
        return read(override)
    with database() as connection:
        return json.loads(connection.execute('SELECT content FROM statements WHERE problem_id=?',
                                            (identity,)).fetchone()[0])


def problem(identity):
    with database() as connection:
        return json.loads(connection.execute('SELECT encoded FROM problems WHERE id=?',
                                            (identity,)).fetchone()[0])


def format_code(code):
    # Mask literals/comments before recognizing a simple, unused for increment.
    masked = re.sub(r'R"([^\s()\\]*)\(.*?\)\1"|"(?:\\.|[^"\\])*"|'
                    r"'(?:\\.|[^'\\])*'|//[^\n]*|/\*.*?\*/",
                    lambda match: ' ' * len(match[0]), code, flags=re.S)
    edits = []
    pattern = r'\bfor\s*\(\s*(?:(?:unsigned|signed|long|short)\s+)*(?:int|char)\s+(\w+)\s*=[^;]*;[^;]*;\s*(\+\+\s*\1)\s*\)'
    for match in re.finditer(pattern, masked):
        edits.append((match.start(2), match.end(2), match[1] + '++'))
    for start, end, value in reversed(edits):
        code = code[:start] + value + code[end:]
    tool = ROOT.parents[1] / '公共工具/代码格式化器/win64/clang-format.exe'
    result = subprocess.run([str(tool), '--assume-filename=main.cpp',
                             '--fail-on-incomplete-format',
                             '--style={BasedOnStyle: LLVM, IndentWidth: 4, ColumnLimit: 100, '
                             'SortIncludes: Never, ReflowComments: false, FixNamespaceComments: false}'],
                            input=code, text=True, encoding='utf-8', capture_output=True,
                            timeout=10, check=True)
    return result.stdout.replace('\r\n', '\n').rstrip() + '\n'


def format_article(text):
    text = FENCE.sub(lambda match: '```cpp\n' + format_code(match[1]) + '```', text)
    return PY_FENCE.sub(lambda match: '```python\n' + format_python(match[1]) + '```', text)


def format_python(code):
    tool = ROOT.parents[1] / '公共工具/代码格式化器/win64/ruff.exe'
    result = subprocess.run([str(tool), 'format', '--isolated', '--no-cache', '--line-length', '100',
                             '--stdin-filename', 'main.py', '--config', "format.quote-style='preserve'", '-'],
                            input=code, text=True, encoding='utf-8', capture_output=True, check=True, timeout=10)
    return result.stdout.replace('\r\n', '\n').rstrip() + '\n'


def program(text):
    blocks = [match[1] for match in FENCE.finditer(text)]
    programs = [code for code in blocks
                if re.search(r'\b(?:int|signed)\s+main\s*\(', code)]
    if not programs:
        programs = [code for code in blocks if re.search(r'\bclass\s+Solution\b', code)]
    if not programs:
        programs = [match[1] for match in PY_FENCE.finditer(text)]
    if len(programs) != 1:
        raise ValueError('Expected one complete reference program, got ' + str(len(programs)))
    return programs[0]


def register(number, rating, knowledge, reason, variants, *, origin=None, cases=None,
             estimate=True, exact=False, empty_sample_reason=None, driver=None, checker=None,
             floating_output=False, preamble=None):
    identity = 'nowcoder-global::' + str(number)
    original = statement(identity)
    item = problem(identity)
    assert 0 < rating <= 2300 and reason.strip() and knowledge
    assert original.get('statementAvailable', True) and original['markdown'].strip()
    ledger_path = CONTENT / 'reviewed.json'
    ledger = read(ledger_path) if ledger_path.exists() else {}
    assert identity not in ledger, identity
    files = {}
    programs = set()
    for variant, text in variants.items():
        text = format_article(text)
        path = CONTENT / ('NC' + str(number) + '.' + variant + '.md')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.rstrip() + '\n', encoding='utf-8')
        files[variant] = str(path.relative_to(ROOT)).replace('\\', '/')
        programs.add(sha(program(text)))
    assert len(programs) == 1, 'Both article variants must use the same verified reference'
    driver_file = None
    if driver:
        driver_path = CONTENT / 'test-drivers' / ('NC' + str(number) + '.cpp')
        driver_path.parent.mkdir(parents=True, exist_ok=True)
        driver_path.write_text(format_code(driver), encoding='utf-8')
        driver_file = str(driver_path.relative_to(ROOT)).replace('\\', '/')
    preamble_file = None
    if preamble:
        preamble_path = CONTENT / 'test-drivers' / ('NC' + str(number) + '.preamble.hpp')
        preamble_path.parent.mkdir(parents=True, exist_ok=True)
        preamble_path.write_text(format_code(preamble), encoding='utf-8')
        preamble_file = str(preamble_path.relative_to(ROOT)).replace('\\', '/')
    ledger[identity] = {'id': identity, 'title': item['title'], 'url': item['url'],
                        'difficulty': rating, 'difficultyEstimated': estimate,
                        'difficultyReason': reason, 'knowledge': knowledge,
                        'statementSha256': sha(original['markdown']),
                        'programSha256': programs.pop(), 'articles': files,
                        'origin': origin, 'cases': cases or [], 'exactOutput': exact,
                        'numericTolerance': 1e-3 if '10^{-3}' in original['markdown'] else 1e-6,
                        'floatingOutput': floating_output,
                        'emptySampleReason': empty_sample_reason, 'testDriver': driver_file,
                        **({'testPreamble': preamble_file} if preamble_file else {}),
                        'outputChecker': checker,
                        'language': 'python3' if PY_FENCE.search(next(iter(variants.values()))) else 'cpp17'}
    write(ledger_path, ledger)


def add(number, rating, knowledge, meaning, idea, body, pitfalls, *,
        complexity='时间与额外空间均为 $O(1)$。', detail=None, declarations='', cases=None,
        exact=False, empty_sample_reason=None, checker=None, floating_output=False):
    code = '#include <bits/stdc++.h>\nusing namespace std;\n\n'
    if declarations:
        code += declarations.strip() + '\n\n'
    code += 'int main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n'
    code += body.strip() + '\n    return 0;\n}\n'
    title = problem('nowcoder-global::' + str(number))['title']
    def article(explanation):
        return ('## ' + title + '\n\n### 题意\n\n' + meaning + '\n\n### 思路\n\n' +
                explanation + '\n\n### 参考代码\n\n```cpp\n' + code + '```\n\n### 复杂度\n\n' +
                complexity + '\n\n### 易错点\n\n' + pitfalls + '\n')
    variants = {'default': article(idea)}
    if detail:
        variants['detailed'] = article(detail)
    register(number, rating, knowledge, idea + ' ' + complexity, variants, cases=cases, exact=exact,
             empty_sample_reason=empty_sample_reason, checker=checker, floating_output=floating_output)


def review_rating(number, rating, reason, *, origin=None, knowledge=None, estimate=True):
    """Persist a full-statement review even when its rating excludes authoring."""
    identity = 'nowcoder-global::' + str(number)
    item, original = problem(identity), statement(identity)
    assert rating > 0 and rating % 100 == 0 and reason.strip()
    path = CONTENT / 'ratings.json'
    values = read(path) if path.exists() else {}
    values[identity] = {'id': identity, 'url': item['url'], 'title': item['title'],
                        'difficulty': rating, 'difficultyEstimated': estimate,
                        'difficultyReason': reason, 'origin': origin,
                        'knowledge': knowledge or [], 'statementSha256': sha(original['markdown'])}
    write(path, values)


def add_python(number, rating, knowledge, meaning, idea, code, pitfalls, *, complexity, cases=None):
    title = problem('nowcoder-global::' + str(number))['title']
    article = ('## ' + title + '\n\n### 题意\n\n' + meaning + '\n\n### 思路\n\n' + idea +
               '\n\n### 参考代码\n\n```python\n' + code.strip() + '\n```\n\n### 复杂度\n\n' +
               complexity + '\n\n### 易错点\n\n' + pitfalls + '\n')
    register(number, rating, knowledge, idea + ' ' + complexity, {'default': article}, cases=cases)


def reviewed_clone(number, source_number, reason, *, rating=None, replacements=None, cases=None):
    ledger = read(CONTENT / 'reviewed.json')
    source = ledger['nowcoder-global::' + str(source_number)]
    target = problem('nowcoder-global::' + str(number))
    variants = {}
    for key, path in source['articles'].items():
        text = (ROOT / path).read_text(encoding='utf-8')
        text = re.sub(r'\A##[^\n]*', '## ' + target['title'], text)
        for old, new in (replacements or {}).items():
            assert old in text, old
            text = text.replace(old, new)
        variants[key] = text
    register(number, rating or source['difficulty'], source['knowledge'], reason, variants,
             origin={'id': source['id'], 'url': source['url'], 'explicitCounterpartReview': reason},
             cases=cases, exact=source.get('exactOutput', False), checker=source.get('outputChecker'),
             floating_output=source.get('floatingOutput', False),
             driver=(ROOT / source['testDriver']).read_text(encoding='utf-8') if source.get('testDriver') else None,
             preamble=(ROOT / source['testPreamble']).read_text(encoding='utf-8') if source.get('testPreamble') else None)


def alias(number, source_id, reason, *, rating=None, cases=None):
    variants = {}
    with database() as connection:
        for variant, table in [('default', 'solutions'), ('detailed', 'detailed_solutions')]:
            row = connection.execute('SELECT * FROM ' + table + ' WHERE problem_id=?',
                                     (source_id,)).fetchone()
            if row:
                text = row['markdown']
                # Preserve original diagrams, including embedded assets.
                images = json.loads(row['images'])
                for name, data in images.items():
                    text = text.replace('](' + name + ')', '](' + data + ')')
                text = re.sub(r'<!-- reusable-foundations:start -->.*?<!-- reusable-foundations:end -->',
                              '', text, flags=re.S)
                text = re.sub(r'\A##[^\n]*', '## ' + problem('nowcoder-global::' + str(number))['title'], text)
                variants[variant] = text
    source = problem(source_id)
    register(number, rating or source['difficulty'], source.get('tags') or [source['knowledge']],
             reason, variants, origin={'id': source_id, 'url': source['url'],
                                      'difficultySource': source.get('difficultySource')},
             estimate=source.get('difficultyEstimated', True), cases=cases)


def output_equal(actual, expected, exact=False, tolerance=1e-6, floating_output=False):
    if exact:
        return actual.replace('\r\n', '\n') == expected.replace('\r\n', '\n')
    a, b = actual.split(), expected.split()
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        # Numeric tolerance only for decimal/scientific output, never integers.
        numeric = re.fullmatch(r'([^\d+-]*)([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)([^\d]*)', y)
        actual_numeric = re.fullmatch(r'([^\d+-]*)([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)([^\d]*)', x)
        if not numeric or not actual_numeric or not (floating_output or '.' in numeric[2] or 'e' in numeric[2].lower()):
            return False
        if (numeric[1], numeric[3]) != (actual_numeric[1], actual_numeric[3]):
            return False
        try:
            if not math.isfinite(float(actual_numeric[2])) or not math.isclose(
                    float(actual_numeric[2]), float(numeric[2]), rel_tol=tolerance, abs_tol=tolerance):
                return False
        except ValueError:
            return False
    return True


def property_check(checker, case, actual):
    if checker == 'falling-pie-walk':
        values = list(map(int, case['input'].split()))
        width, height = values[:2]
        reward = {}
        for t, x, speed, score in zip(values[2::4], values[3::4], values[4::4], values[5::4]):
            if (height - 1) % speed == 0:
                key = (t + (height - 1) // speed, x)
                reward[key] = reward.get(key, 0) + score
        try:
            result = list(map(int, actual.split()))
        except ValueError:
            return False
        if not result or result[0] != int(case['output'].split()[0]):
            return False
        position = (width + 1) // 2
        score = reward.get((0, position), 0)
        for t, move in enumerate(result[1:], 1):
            if not -2 <= move <= 2:
                return False
            position += move
            if not 1 <= position <= width:
                return False
            score += reward.get((t, position), 0)
        return score == result[0]
    if checker == 'eight-puzzle-path':
        state = list(''.join(case['input'].split()))
        digits = [int(x) for x in state if x != 'x']
        odd = sum(a > b for i, a in enumerate(digits) for b in digits[i + 1:]) % 2
        result = actual.strip()
        if result == 'unsolvable':
            return bool(odd)
        if odd:
            return False
        for move in result:
            if move not in 'udlr':
                return False
            blank = state.index('x')
            r, c = divmod(blank, 3)
            dr, dc = {'u': (-1, 0), 'd': (1, 0), 'l': (0, -1), 'r': (0, 1)}[move]
            rr, cc = r + dr, c + dc
            if not (0 <= rr < 3 and 0 <= cc < 3):
                return False
            other = rr * 3 + cc
            state[blank], state[other] = state[other], state[blank]
        return ''.join(state) == '12345678x'
    if checker == 'language-connectivity-books':
        data = iter(map(int, case['input'].split()))
        n, m = next(data), next(data)
        parent = list(range(n + m))
        def root(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def unite(a, b):
            parent[root(a)] = root(b)
        for cow in range(n):
            for _ in range(next(data)):
                unite(cow, n + next(data) - 1)
        needed = len({root(cow) for cow in range(n)}) - 1
        try:
            values = list(map(int, actual.split()))
        except ValueError:
            return False
        if not values or values[0] != needed or len(values) != 1 + 2 * needed:
            return False
        for language, cow in zip(values[1::2], values[2::2]):
            if not (1 <= language <= m and 1 <= cow <= n):
                return False
            unite(cow - 1, n + language - 1)
        return len({root(cow) for cow in range(n)}) == 1
    if checker == 'chocolate-eating-schedule':
        numbers = list(map(int, case['input'].split()))
        n, days = numbers[:2]
        chocolates = numbers[2:]
        try:
            result = list(map(int, actual.split()))
        except ValueError:
            return False
        if len(result) != n + 1 or result[0] != int(case['output'].split()[0]):
            return False
        plan = result[1:]
        if plan != sorted(plan) or any(not 1 <= d <= days for d in plan):
            return False
        meals = [0] * (days + 1)
        for value, day in zip(chocolates, plan):
            meals[day] += value
        happiness, minimum = 0, math.inf
        for day in range(1, days + 1):
            happiness = happiness // 2 + meals[day]
            minimum = min(minimum, happiness)
        return minimum >= result[0]
    if checker == 'maximum-popcount-in-interval':
        from functools import lru_cache
        numbers = list(map(int, case['input'].split()))
        try:
            answers = list(map(int, actual.split()))
        except ValueError:
            return False
        if len(answers) != numbers[0]:
            return False
        for i, answer in enumerate(answers):
            lower, upper = numbers[1 + 2 * i:3 + 2 * i]
            if not lower <= answer <= upper:
                return False
            @lru_cache(None)
            def best(bit, tight_lower, tight_upper):
                if bit < 0:
                    return 0
                low = (lower >> bit) & 1 if tight_lower else 0
                high = (upper >> bit) & 1 if tight_upper else 1
                return max(d + best(bit - 1, tight_lower and d == low, tight_upper and d == high)
                           for d in range(low, high + 1))
            if answer.bit_count() != best(60, True, True):
                return False
        return True
    if checker == 'maximum-square-corners':
        tokens = case['input'].split()
        n, rows = int(tokens[0]), tokens[1:]
        try:
            values = list(map(int, actual.split()))
        except ValueError:
            return False
        if len(values) != 8:
            return False
        points = [(values[i] - 1, values[i + 1] - 1) for i in range(0, 8, 2)]
        if len(set(points)) != 4 or any(not (0 <= r < n and 0 <= c < n) or rows[r][c] != '#'
                                       for r, c in points):
            return False
        distances = sorted((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                           for a, b in itertools.combinations(points, 2))
        if not (distances[0] > 0 and len(set(distances[:4])) == 1 and
                distances[4] == distances[5] == 2 * distances[0]):
            return False
        occupied = {(r, c) for r in range(n) for c in range(n) if rows[r][c] == '#'}
        maximum_diagonal = 0
        for a, b in itertools.combinations(occupied, 2):
            rsum, csum = a[0] + b[0], a[1] + b[1]
            dr, dc = a[0] - b[0], a[1] - b[1]
            if (rsum + dc) % 2 or (csum - dr) % 2:
                continue
            c = ((rsum + dc) // 2, (csum - dr) // 2)
            d = ((rsum - dc) // 2, (csum + dr) // 2)
            if c in occupied and d in occupied:
                maximum_diagonal = max(maximum_diagonal, dr * dr + dc * dc)
        return distances[4] == maximum_diagonal
    if checker == 'weighted-median-index':
        try:
            values = list(map(int, case['input'].split()))
            answer = int(actual.strip()) - 1
        except ValueError:
            return False
        n = values[0]
        if not 0 <= answer < n:
            return False
        positions, weights = values[1:n + 1], values[n + 1:]
        cost = sum(abs(x - positions[answer]) * w for x, w in zip(positions, weights))
        current = sum((x - positions[0]) * w for x, w in zip(positions, weights))
        best, left, total = current, weights[0], sum(weights)
        for i in range(1, n):
            current += (positions[i] - positions[i - 1]) * (2 * left - total)
            best = min(best, current)
            left += weights[i]
        return cost == best
    if checker == 'all-permutations-1-to-8':
        rows = actual.splitlines()
        if len(rows) != math.factorial(8) or any(x != x.rstrip() for x in rows):
            return False
        previous = None
        for line in rows:
            try:
                values = tuple(map(int, line.split()))
            except ValueError:
                return False
            if sorted(values) != list(range(1, 9)) or previous is not None and previous >= values:
                return False
            previous = values
        return True
    if checker == 'any-valid-triangle':
        from collections import Counter
        numbers = list(map(int, case['input'].split()))
        a = numbers[1:]
        if actual.strip() == 'No solution':
            return not any(sum(t) > 2 * max(t) for t in itertools.combinations(a, 3))
        try:
            values = list(map(int, actual.split()))
        except ValueError:
            return False
        return (len(values) == 3 and not (Counter(values) - Counter(a))
                and sum(values) > 2 * max(values))
    from nowcoder_extra_checkers import check_extra
    result = check_extra(checker, case, actual)
    if result is not None:
        return result
    raise ValueError('Unknown property checker: ' + str(checker))


def validate_one(entry):
    number = entry['id'].split('::')[-1]
    folder = OUT / 'compiled' / number
    folder.mkdir(parents=True, exist_ok=True)
    article = (ROOT / entry['articles']['default']).read_text(encoding='utf-8')
    code = program(article)
    original = statement(entry['id'])
    assert sha(original['markdown']) == entry['statementSha256']
    assert sha(code) == entry['programSha256']
    python = entry.get('language') == 'python3'
    assert (format_python(code) if python else format_code(code)) == code, number
    for variant, file in entry['articles'].items():
        assert program((ROOT / file).read_text(encoding='utf-8')) == code, number
    source, executable = folder / ('main.py' if python else 'main.cpp'), folder / 'main.exe'
    driver = (ROOT / entry['testDriver']).read_text(encoding='utf-8') if entry.get('testDriver') else ''
    assert python or re.search(r'\b(?:int|signed)\s+main\s*\(', code + driver), 'Missing test driver'
    preamble = (ROOT / entry['testPreamble']).read_text(encoding='utf-8') if entry.get('testPreamble') else ''
    source.write_text(preamble + '\n' + code + '\n' + driver, encoding='utf-8')
    compiler = sys.executable if python else shutil.which('g++')
    command = ([compiler, '-I', '-m', 'py_compile', str(source)] if python else
               [compiler, '-std=c++17', '-O2', '-Wall', '-Wextra', str(source), '-o', str(executable)])
    result = subprocess.run(command, capture_output=True, timeout=90)
    (folder / 'compiler.txt').write_bytes(result.stderr)
    if result.returncode:
        return {'id': entry['id'], 'ok': False, 'compileError': result.stderr.decode('utf8', 'replace')[:2000]}
    original_cases = original.get('samples', [])
    omitted = []
    if entry.get('emptySampleReason'):
        omitted = [x for x in original_cases if not x['input'] and not x['output']]
        original_cases = [x for x in original_cases if x not in omitted]
        assert omitted and entry.get('cases'), 'An empty source sample needs an explicit replacement'
    cases = [*original_cases, *entry.get('cases', [])]
    results = []
    for case in cases:
        try:
            run = subprocess.run([compiler, '-I', str(source)] if python else [str(executable)], input=case['input'].encode('utf-8'),
                                 capture_output=True, timeout=5)
            actual = run.stdout.decode('utf8', 'replace')
            checker = entry.get('outputChecker')
            ok = run.returncode == 0 and (property_check(checker, case, actual) if checker else
                    output_equal(actual, case['output'], entry['exactOutput'], entry.get('numericTolerance', 1e-6),
                                 entry.get('floatingOutput', False)))
            results.append({'name': case.get('name', 'boundary'), 'ok': ok,
                            'inputSha256': sha(case['input']), 'expectedSha256': sha(case['output']),
                            **({'propertyChecker': checker} if checker else {}),
                            **({} if ok else {'input': case['input'], 'expected': case['output'],
                                            'actual': actual[:2000], 'returncode': run.returncode})})
        except subprocess.TimeoutExpired:
            results.append({'name': case.get('name', 'boundary'), 'ok': False, 'timeout': True})
    return {'id': entry['id'], 'ok': bool(cases) and all(x['ok'] for x in results),
            'statementSha256': entry['statementSha256'], 'programSha256': sha(code),
            'articleSha256': {k: sha((ROOT / v).read_bytes()) for k, v in entry['articles'].items()},
            'compiler': compiler, 'cases': results, 'officialSubmissionSent': False,
            'omittedEmptySamples': len(omitted), 'emptySampleReason': entry.get('emptySampleReason'),
            'entrySha256': sha(json.dumps(entry, ensure_ascii=False, sort_keys=True))}


def validate():
    entries = list(read(CONTENT / 'reviewed.json').values())
    previous = {x['id']: x for x in read(OUT / 'validation.json')} if (OUT / 'validation.json').exists() else {}
    pending, reused = [], []
    for entry in entries:
        prior = previous.get(entry['id'], {})
        article_hashes = {k: sha((ROOT / v).read_bytes()) for k, v in entry['articles'].items()}
        if (prior.get('ok') and prior.get('entrySha256') == sha(json.dumps(entry, ensure_ascii=False, sort_keys=True))
                and prior.get('articleSha256') == article_hashes
                and sha(statement(entry['id'])['markdown']) == prior.get('statementSha256')):
            reused.append(prior)
        else:
            pending.append(entry)
    with ThreadPoolExecutor(max_workers=3) as pool:
        reports = reused + list(pool.map(validate_one, pending))
    write(OUT / 'validation.json', reports)
    print(json.dumps({'problems': len(reports), 'passed': sum(x['ok'] for x in reports),
                      'newlyValidated': len(pending), 'unchangedReceiptsReused': len(reused),
                      'cases': sum(len(x.get('cases', [])) for x in reports),
                      'failures': [x for x in reports if not x['ok']]}, ensure_ascii=False))
    return int(any(not x['ok'] for x in reports))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['validate'])
    args = parser.parse_args()
    return validate()


if __name__ == '__main__':
    raise SystemExit(main())
