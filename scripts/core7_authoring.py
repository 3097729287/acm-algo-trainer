"""Authored route editorials, with one validated program per method and two texts.

Public content is emitted only for explicit authored entries. Missing route
entries stay pending in the task ledger; they are never filled with templates.
"""
from dataclasses import dataclass, field
from pathlib import Path
import base64
from collections import Counter
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.backups/core7-editorials-20261030'
CONTENT = ROOT / 'data/core7-editorials'
SPECS = []


@dataclass
class Method:
    pid: str
    key: str
    title: str
    meaning: str
    brief: str
    detail: str
    code: str
    pitfalls: str
    complexity: str
    tags: list
    lessons: list = field(default_factory=list)
    cases: list = field(default_factory=list)
    images: dict = field(default_factory=dict)
    exact: bool = False
    checker: str = ''
    interactive: str = ''


def program(body, declarations=''):
    return '#include <bits/stdc++.h>\nusing namespace std;\n' + declarations.strip() + '\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n' + body.strip() + '\n    return 0;\n}\n'


def add(pid, title, meaning, brief, detail, body, pitfalls, complexity='时间与额外空间均为 $O(1)$。',
        tags=None, lessons=None, key='direct', declarations='', cases=None, exact=False, checker='', interactive=''):
    SPECS.append(Method(pid, key, title, meaning, brief, detail, program(body, declarations),
                        pitfalls, complexity, tags or ['模拟'], lessons or [], cases or [], exact=exact, checker=checker,interactive=interactive))


def load_all():
    if not SPECS:
        import core7_stage01
        import core7_stage02
        import core7_stage02_simulation
        import core7_stage02_greedy
        import core7_stage02_recurrence
        import core7_stage02_prefix
        import core7_stage02_binary
        import core7_stage02_twopointers
        import core7_stage02_interactive
        from core7_figures import attach_figures
        attach_figures(SPECS)
        from core7_figures_greedy import attach_figures as greedy_figures
        greedy_figures(SPECS)
        from core7_figures_recurrence import attach_figures as recurrence_figures
        recurrence_figures(SPECS)
        from core7_figures_prefix import attach_figures as prefix_figures
        prefix_figures(SPECS)
        from core7_figures_binary import attach_figures as binary_figures
        binary_figures(SPECS)
        for spec in SPECS:
            spec.tags=['线性 DP' if tag=='DP' else tag for tag in spec.tags]
            if spec.pid=='P5732':spec.tags=['递推']
            if spec.pid=='P1553':spec.lessons=['io-basics','strings','string-tools','functions']
            if spec.pid in ['P1597','P1449','P1603','P1957','P5734','P1161']:
                spec.lessons.append('string-tools')
            spec.lessons=list(dict.fromkeys(spec.lessons))
    return SPECS


def source_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def verification_footer(record):
    if record.get('interactive'):
        live=record['interactive']
        return (f"本地 C++17 编译、{live['liveScenarios']} 个真实交互场景与 {record['independentCases']} 组转录重放通过；核对主动刷新、合法询问与问数上限。\n"
                "官方样例是对话，已按样例秘密场景另行交互验证，未当作普通固定输入输出比较。\n"
                "正文参考程序与源码逐字核对；没有向原站提交。\n")
    return f'本地 C++17 编译、{record["samples"]} 组原站样例与 {record["independentCases"]} 组独立边界/小域校验通过。\n正文参考程序与源码逐字核对；没有向原站提交。\n'


def roster_entries():
    scope=json.loads((OUT/'scope.json').read_text('utf-8'))
    # The problem code is an authoring key. Keep every existing database alias.
    entries={entry['url'].rstrip('/').split('/')[-1]:entry for entry in scope}
    assert len(entries)==len(scope),'Ambiguous problem-code mapping'
    return entries


def statement_path(pid):
    identity=roster_entries()[pid]['id']
    return OUT/'statements'/(re.sub(r'[:<>/\\|?*]','_',identity)+'.json')


def display_id(pid):
    return pid[3:].replace('_','').upper() if pid.startswith('AT_') else pid


def lesson_data():
    from refresh_editorial_teaching import lesson_sources, inline_lesson
    values = lesson_sources()
    return values, inline_lesson


def article(spec, title, url, detailed, sources, inline):
    label=display_id(spec.pid)
    text = f'## {label}. {title}\n\n> 原题：[{label}]({url})\n> 解法：{spec.title} · C++17\n\n### 题意\n\n{spec.meaning}\n\n'
    images = dict(spec.images)
    if spec.lessons:
        text += '<!-- reusable-foundations:start -->\n\n'
        for name in spec.lessons:
            block=inline(name,sources[name])
            for key,data in sources[name]['images'].items():
                destination=key
                if key in images and images[key]!=data:
                    asset=Path(key)
                    destination=str(asset.with_name(asset.stem+'-core7-'+source_hash(data)[:10]+asset.suffix)).replace('\\','/')
                    block=block.replace(']('+key+')',']('+destination+')')
                images[destination]=data
            text += block + '\n\n'
        text += '<!-- reusable-foundations:end -->\n\n'
    text += '### 思路\n\n' + (spec.detail if detailed else spec.brief) + '\n\n' + spec.complexity
    text += '\n\n### 参考代码\n\n```cpp\n' + spec.code + '```\n\n### 易错点\n\n' + spec.pitfalls + '\n'
    import sys
    sys.path.insert(0,str(Path.home()/'.dsh/tools'))
    import unify_latex
    text=unify_latex.process(text,Counter())
    # Normalize title mathematics separately so a code such as P8649 is never
    # absorbed into the formula that begins its lowercase problem title.
    heading=f'## {label}. '+unify_latex.process(title,Counter())
    text=re.sub(r'^## [^\n]+',lambda _:heading,text,count=1)
    return {'markdown': text, 'images': images}


def generate():
    import sys
    sys.path.insert(0,str(Path.home()/'.dsh/tools'))
    specs = load_all()
    sources, inline = lesson_data()
    scope = json.loads((OUT / 'scope.json').read_text('utf-8'))
    roster = roster_entries()
    seen = set()
    package = []
    verified={(r['pid'],r['method']):r for r in json.loads((OUT/'verification.json').read_text('utf-8'))} if (OUT/'verification.json').exists() else {}
    for spec in specs:
        assert (spec.pid, spec.key) not in seen
        seen.add((spec.pid, spec.key))
        entry = roster[spec.pid]
        # A lowercase title immediately after "A." is misread as a formula by
        # the old DSH normalizer. This affects only its interchange envelope.
        import unify_latex
        probe=unify_latex.process('## A. '+entry['title'],Counter())
        export_title=('题目：' if (entry['title'][:1].isascii() and entry['title'][:1].islower()) or not probe.startswith('## A. ') else '')+entry['title']
        folder = CONTENT / spec.pid / spec.key
        folder.mkdir(parents=True, exist_ok=True)
        cpp = folder / 'a.cpp'
        cpp.write_text(spec.code, encoding='utf-8')
        variants = {}
        for detailed, name in [(False, 'default'), (True, 'detailed')]:
            value = article(spec, entry['title'], entry['url'], detailed, sources, inline)
            assert len(re.findall(r'^```cpp\n', value['markdown'], re.M)) == 1
            variants[name] = value
            # Export self-contained reading files for the existing DSH checker.
            path = folder / (name + '.md')
            catalog = ' + '.join(spec.tags)
            envelope = f'# {display_id(spec.pid)} {spec.title} 题解\n\n## 目录\n\n| 题号 | 题名 | 考点 | 难度 |\n|---|---|---|---|\n| A | {export_title} | {catalog} | {entry["difficulty"]} |\n\n'
            record=verified.get((spec.pid,spec.key))
            footer=''
            if record and record.get('passed') and record['programSha256']==source_hash(spec.code):
                footer='\n## 实测记录\n\n'+verification_footer(record)
            exported=re.sub(r'^## [^\n]+',f'## A. {export_title}',value['markdown'],count=1)
            import sys
            sys.path.insert(0,str(Path.home()/'.dsh/tools'))
            import unify_latex
            path.write_text(unify_latex.process(envelope+exported+footer,Counter()), encoding='utf-8')
            for key, data in value['images'].items():
                target = folder / key
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(base64.b64decode(data.split(',', 1)[1]))
        package.append({'problemId': entry['id'], 'pid': spec.pid, 'method': spec.key, 'title': spec.title,
                        'tags': spec.tags, 'lessons': spec.lessons, 'variants': variants,
                        'programSha256': source_hash(spec.code)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'authored.json').write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'authoredProblems': len({s.pid for s in specs}), 'methods': len(specs), 'articles': len(specs)*2, 'pendingProblems': len(scope)-len({s.pid for s in specs})}, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    sys.modules['core7_authoring'] = sys.modules[__name__]
    generate()
