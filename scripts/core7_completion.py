"""Reviewed additions to the existing Luogu route; no personal data writes."""
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import math
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.backups/core7-complete-20261108'
ENTRIES = {}
_LOADED = False


@dataclass
class Entry:
    pid: str
    method: str
    overview: str
    explanation: str
    complexity: str
    pitfalls: str
    body: str
    declarations: str = ''
    cases: list = field(default_factory=list)
    checker: str = ''
    images: dict = field(default_factory=dict)
    interactive: str = ''


def add(pid, method, overview, explanation, complexity, pitfalls, body, declarations='', cases=None, checker='', interactive=''):
    assert pid not in ENTRIES, pid
    ENTRIES[pid] = Entry(pid, method, overview, explanation, complexity, pitfalls,
                         body, declarations, cases or [], checker, interactive=interactive)


DSU = r'''
struct DSU {
    vector<int> p, size;
    explicit DSU(int n): p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) { while (p[x] != x) { p[x] = p[p[x]]; x = p[x]; } return x; }
    bool join(int a, int b) { a = find(a); b = find(b); if (a == b) return false;
        if (size[a] < size[b]) swap(a, b); p[b] = a; size[a] += size[b]; return true; }
};
'''

SCC = r'''
struct SCC {
    int n, count = 0; vector<vector<int>> g, rev; vector<int> component;
    explicit SCC(int n): n(n), g(n), rev(n), component(n, -1) {}
    void edge(int a, int b) { g[a].push_back(b); rev[b].push_back(a); }
    void build() {
        vector<char> seen(n); vector<int> order;
        for (int start = 0; start < n; start++) if (!seen[start]) {
            vector<pair<int,int>> st = {{start, 0}}; seen[start] = true;
            while (!st.empty()) { int v = st.back().first; int &i = st.back().second;
                if (i < (int)g[v].size()) { int u = g[v][i++];
                    if (!seen[u]) { seen[u] = true; st.push_back({u,0}); }
                } else { order.push_back(v); st.pop_back(); }
            }
        }
        reverse(order.begin(), order.end());
        for (int start : order) if (component[start] < 0) {
            vector<int> st = {start}; component[start] = count;
            while (!st.empty()) { int v = st.back(); st.pop_back();
                for (int u : rev[v]) if (component[u] < 0) { component[u] = count; st.push_back(u); }
            } count++;
        }
    }
};
'''

FENWICK = r'''
struct Fenwick {
    int n; vector<long long> t;
    explicit Fenwick(int n): n(n), t(n+1) {}
    void add(int x, long long v) { for (; x <= n; x += x & -x) t[x] += v; }
    long long sum(int x) const { long long s = 0; for (; x; x -= x & -x) s += t[x]; return s; }
};
'''

BIG = r'''
struct Big {
    static const int base=1000000000; vector<int>d;
    Big(long long x=0){do{d.push_back(x%base);x/=base;}while(x);}
    explicit Big(string s){for(int r=s.size();r>0;r-=9)d.push_back(stoi(s.substr(max(0,r-9),min(9,r))));trim();}
    void trim(){while(d.size()>1&&d.back()==0)d.pop_back();}
    void multiply(long long x){long long carry=0;for(int &v:d){long long z=v*x+carry;v=z%base;carry=z/base;}while(carry){d.push_back(carry%base);carry/=base;}trim();}
    long long divide(long long x){long long rem=0;for(int i=(int)d.size()-1;i>=0;i--){long long z=rem*base+d[i];d[i]=z/x;rem=z%x;}trim();return rem;}
    void add(long long x){long long carry=x;for(int i=0;carry;i++){if(i==(int)d.size())d.push_back(0);long long z=d[i]+carry;d[i]=z%base;carry=z/base;}}
    void addBig(const Big&b){int n=max(d.size(),b.d.size());d.resize(n,0);long long carry=0;for(int i=0;i<n;i++){long long z=(long long)d[i]+(i<(int)b.d.size()?b.d[i]:0)+carry;d[i]=z%base;carry=z/base;}if(carry)d.push_back(carry);}
    void subtract(const Big&b){int borrow=0;for(int i=0;i<(int)d.size();i++){long long z=(long long)d[i]-(i<(int)b.d.size()?b.d[i]:0)-borrow;borrow=z<0;if(borrow)z+=base;d[i]=z;}trim();}
    friend ostream&operator<<(ostream&out,const Big&b){out<<b.d.back();for(int i=(int)b.d.size()-2;i>=0;i--)out<<setw(9)<<setfill('0')<<b.d[i];return out;}
};
'''


def load():
    global _LOADED
    if _LOADED:return ENTRIES
    import core7_completion_graph
    import core7_completion_data
    import core7_completion_math
    import core7_completion_strings
    import core7_completion_dp
    import core7_completion_misc
    import core7_completion_actual
    import core7_completion_actual_graph
    import core7_completion_actual_math
    import core7_completion_actual_dp
    import core7_completion_actual_strings
    import core7_completion_actual_dp2
    import core7_completion_actual_data
    import core7_completion_actual_probability
    import core7_completion_actual_misc
    import core7_completion_actual_advanced
    import core7_completion_actual_interactive
    from core7_completion_visuals import attach
    attach(ENTRIES)
    from core7_completion_cases import attach as attach_cases
    attach_cases(ENTRIES)
    from core7_completion_actual_cases import attach as actual_cases
    actual_cases(ENTRIES)
    _LOADED=True
    return ENTRIES


def program(entry):
    raw = '#include <bits/stdc++.h>\nusing namespace std;\n' + entry.declarations
    raw += '\nint main() {\nios::sync_with_stdio(false);\ncin.tie(nullptr);\n' + entry.body + '\nreturn 0;\n}\n'
    tool = ROOT.parents[1] / '版本/最新版/程序/resources/formatters/clang-format.exe'
    result = subprocess.run([str(tool), '--assume-filename=main.cpp',
        '--style={BasedOnStyle: LLVM, IndentWidth: 4, ColumnLimit: 100, SortIncludes: Never, ReflowComments: false, FixNamespaceComments: false}'],
        input=raw, text=True, encoding='utf8', capture_output=True, check=True)
    return result.stdout.replace('\r\n', '\n')


def sha(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', default='')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    entries = load()
    scope = {p['pid']: p for p in json.loads((OUT/'inventory.json').read_text('utf8'))['problems']}
    for p in json.loads((OUT/'scope.json').read_text('utf8')):
        scope.setdefault(p.get('pid',p['url'].split('/')[-1]),p)
    # Preserve the original route as well when the current automatic selection changes.
    for p in json.loads((ROOT/'data/core7-editorials/requested-roster.json').read_text('utf8')):
        scope.setdefault(p['url'].split('/')[-1], p)
    statements = json.loads((OUT/'statements.json').read_text('utf8'))
    records = []
    for pid, entry in entries.items():
        if args.only and pid not in args.only.split(','): continue
        item = scope[pid]; folder = OUT/'programs'/pid; folder.mkdir(parents=True, exist_ok=True)
        code = program(entry); cpp = folder/'main.cpp'; cpp.write_text(code, encoding='utf8',newline='\n')
        exe = folder/'main.exe'
        built = subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', str(cpp), '-o', str(exe)],
                               capture_output=True, text=True, encoding='utf8')
        if built.returncode:
            print(pid, 'COMPILE FAILED', built.stderr[-4000:], flush=True)
            records.append({'pid':pid,'passed':False,'phase':'compile','diagnostics':built.stderr})
            continue
        all_samples = statements.get(pid, {}).get('samples', [])
        # Some original statements list attachment filenames, not executable input.
        unavailable_samples = [s for s in all_samples if re.match(r'^\s*见(?:附|选手)',s['input'])]
        samples = [s for s in all_samples if s not in unavailable_samples]
        if entry.interactive: samples=[]
        tests = [(s['input'],s['output']) for s in samples] + entry.cases
        failures = []
        protocol_report=[]
        if entry.interactive:
            from core7_completion_interactive_check import validate
            protocol_report=validate(entry.interactive,exe)
            failures.extend(r for r in protocol_report if not r['passed'])
        for inp, expected in tests:
            try:
                ran = subprocess.run([str(exe)], input=inp, capture_output=True, text=True, encoding='utf8', timeout=12)
                if entry.checker:
                    from core7_completion_checkers import check
                    valid = check(entry.checker, inp, ran.stdout, expected)
                else:
                    left,right=ran.stdout.split(),expected.split()
                    valid=len(left)==len(right) and all(a==b or numeric_equal(a,b) for a,b in zip(left,right))
                if ran.returncode or not valid: failures.append({'input': inp, 'expected':expected, 'actual':ran.stdout, 'returncode':ran.returncode})
            except subprocess.TimeoutExpired: failures.append({'input': inp, 'timeout':True})
        record={'pid':pid, 'id':item['id'], 'programSha256':sha(code), 'samples':len(samples),
                'independentCases':len(entry.cases), 'unavailableSamples':unavailable_samples,
                'interactiveExamples':len(all_samples) if entry.interactive else 0,
                'protocolCases':protocol_report,
                'passed':not failures, 'failures':failures}
        record['originalJudgeSubmissions']=0
        if pid=='P1766':record['semanticLimitation']='仅核验非水平、非竖直且每次首次命中唯一的轨道；同时命中规则原题未定义。'
        if pid=='P1858':record['semanticLimitation']='仅核验至少有 K 种装满方案的输入；不足 K 种时原题未定义输出。'
        records.append(record); print(pid, 'PASS' if not failures else 'FAIL', len(tests)+len(protocol_report), flush=True)
        (folder/'verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        if failures: continue
        header=f"## {pid} {item['title']}\n\n原题：[{pid}]({item['url']})\n\n"
        tail=f'\n\n### 复杂度\n\n{entry.complexity}\n\n### 参考代码\n\n```cpp\n{code}```\n\n### 实现提醒\n\n{entry.pitfalls}\n'
        variants={
            'default':header+'### 思路\n\n'+entry.overview+tail,
            'detailed':header+'### 从问题到算法\n\n'+entry.explanation+tail,
        }
        for name,text in variants.items(): (folder/(name+'.md')).write_text(text,encoding='utf8')
        if args.apply:
            public=ROOT/'data/core7-completion'/pid; public.mkdir(parents=True,exist_ok=True)
            (public/'main.cpp').write_text(code,encoding='utf8',newline='\n')
            (public/'entry.json').write_text(json.dumps({'problemId':item['id'], 'method':entry.method,
                'variants':variants, 'images':entry.images, 'validation':record},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            import base64
            for name,data in entry.images.items():
                asset=public/name;asset.parent.mkdir(parents=True,exist_ok=True)
                asset.write_bytes(base64.b64decode(data.split(',',1)[1]))
    (OUT/'last-verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if any(not r['passed'] for r in records): raise SystemExit(1)


def numeric_equal(a,b):
    if not any(c in (a+b).lower() for c in '.e'): return False
    try:
        x,y=float(a),float(b)
        return math.isfinite(x) and math.isfinite(y) and abs(x-y) <= 1e-6*max(1,abs(y))
    except ValueError: return False


if __name__ == '__main__':
    import math
    sys.modules['core7_completion']=sys.modules[__name__]
    main()
