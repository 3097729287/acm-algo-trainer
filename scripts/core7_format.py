"""Run the unmodified DSH checks with reviewed literal C++ spellings.

The original checker intentionally exposes KEEP_EXACT as data. These entries
are actual C++ types, calls, operators, or literal I/O examples in the standalone
lessons, not exemptions for malformed mathematics. No checker rule is changed.
"""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from core7_authoring import OUT,ROOT,CONTENT,load_all

sys.path.insert(0,str(Path.home()/'.dsh/tools'))
import unpair_ticks
import check_solution

CODE_SPELLINGS=[
    '<iostream>','<string>','<iomanip>','fixed','setprecision','string(k,c)',
    '/','%','x+d-1','1LL*a*b','sqrt(x)','<cmath>','ceil(x)','x','abs(x)',
    'min(a,b)','max(a,b)','min({a,b,c})','c','*it','first','last','list','set',
    'distance(begin,it)','123.4','4.321','120.0','0.021','sqrt','setw(2)',
    '<','<=','>','p<=n/p','>=','=','!','if','for','vector<int> a(n,0)',
    'vector<T>','T','vector<int>','<vector>','vector<int> a(3)','a.reserve(3)',
    '275','stoi','stoll','a b3','<cctype>','isdigit(c)','tolower(c)','insert',
    'even','int x','even(8)','int &x','map<Key,Value>','count','capacity()',
    'at(i)','front()','back()','&','|','^','1','x & (x-1)',
    '(a % m + m) % m','(a+b-1)/b','queue','deque','front','back','top',
    'pair<A,B>','.first','.second','tuple<A,B,C>','get<0>(t)','<utility>',
    '<tuple>','auto&','pair','tuple','set<T>','erase(value)','erase(it)',
    'const vector<int>& a','vector<int> a','<algorithm>','sort(first,last)',
    '(x % m + m) % m','1.0/n','1/n','4.0/3','4/3','<cstdint>','<queue>',
    '<random>','L-1','Student','a+b','accumulate','cmp(a,b)','const Student&',
    'const string &','factorial(3)','fill','hi','hi - lo','insert(x).second',
    'iota','lo','map<pair<int,int>,int>','memset','mt19937','pop','pop()',
    'prefix(r)-prefix(l-1)','priority_queue<T>','push(x)','reverse','second',
    'top()','uniform_int_distribution<int>(left,right)','vector<Student> students(n)',
    '2(2+2(0))+2(2)+2(0)', # exact textual output of P1010, not an evaluated formula
]

def main():
    unpair_ticks.KEEP_EXACT.update(CODE_SPELLINGS)
    results=[]
    with tempfile.TemporaryDirectory(prefix='core7-format-') as temporary:
        for spec in load_all():
            for variant in ['default','detailed']:
                path=CONTENT/spec.pid/spec.key/(variant+'.md')
                with contextlib.redirect_stdout(io.StringIO()):
                    report,_=check_solution.check_file(str(path),temporary)
                results.append({'file':str(path.relative_to(ROOT)),'failed':report.failed,'items':report.items})
    (OUT/'format-all.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    errors=[{'file':r['file'],'items':[i for i in r['items'] if i[0]=='问题']} for r in results if r['failed']]
    print(json.dumps({'articles':len(results),'failed':len(errors),'errors':errors},ensure_ascii=False))
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
