"""Compile and execute the new language examples with explicit expected results."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from core7_authoring import ROOT,OUT

checks={
    'decimal-addition': [('', '', 'assert(decimal_add("998","27")=="1025");assert(decimal_add("0","0")=="0");assert(decimal_add("999","1")=="1000");')],
    'binary-lifting': [('', '', 'assert(u==4);assert(up[2][1]==5);assert(up[2][4]==0);')],
    'io-basics': [('20 30\n','50\n','')],
    'basic-arithmetic': [('', '', 'assert(money==103 && count==5 && rest==8 && average==2.5);')],
    'basic-control': [('', 'B',''),('','10',''),('','','assert(x==1 && times==3);')],
    'arrays': [('', '', 'assert(sum==12);')],
    'functions': [('', '', 'assert(a && !b);')],
    'structures': [('', 'Lin 95', '')],
    'string-tools': [('', '', 'assert(x==275 && y==10000000000LL && equation=="275+125=400");'),
                     ('', '', "assert(c=='a' && digit);"),
                     ('', '', 'assert(text=="bXXcd" && last==\'d\' && where==string::npos && first==3);')],
    'random-selection': [('', '', 'assert(index>=2 && index<=8);')],
    'lex-permutation': [('', '', 'assert(count==6 && a==vector<int>({1,2,3}));')],
    'big-integers': [('', '', 'assert(digits==vector<int>({4,8,0,6}));')],
    'unsigned64': [('', '', 'assert(zero==0 && wrapped==top && product==1000000000000000000ULL);')],
}
results=[]
with tempfile.TemporaryDirectory(prefix='core7-language-') as temporary:
    folder=Path(temporary)
    for name,cases in checks.items():
        text=(ROOT/'docs/foundations'/(name+'.md')).read_text('utf-8')
        blocks=re.findall(r'^```cpp\s*\n(.*?)^```',text,re.M|re.S)
        assert len(blocks)==len(cases),name
        for i,(block,(inp,expected,extra)) in enumerate(zip(blocks,cases)):
            if 'int main(' in block:
                code=block
                if extra:
                    at=code.rfind('}');code=code[:at]+extra+'\n'+code[at:]
                if '#include' not in code:code='#include <bits/stdc++.h>\nusing namespace std;\n'+code
            else:code='#include <bits/stdc++.h>\nusing namespace std;\nint main(){\n'+block+'\n'+extra+'\n}\n'
            if name=='decimal-addition':code='#include <bits/stdc++.h>\nusing namespace std;\n'+block+'\nint main(){'+extra+'}\n'
            code='#include <cassert>\n'+code
            source=folder/(name+str(i)+'.cpp');exe=source.with_suffix('.exe');source.write_text(code,encoding='utf-8')
            compiled=subprocess.run([shutil.which('g++'),'-std=c++17','-O2',str(source),'-o',str(exe)],capture_output=True,text=True,encoding='utf-8')
            assert compiled.returncode==0,compiled.stderr
            ran=subprocess.run([str(exe)],input=inp,capture_output=True,text=True,encoding='utf-8',timeout=4)
            assert ran.returncode==0 and ran.stdout==expected,(name,i,ran.stdout,ran.stderr)
            results.append({'lesson':name,'snippet':i+1,'passed':True})
(OUT/'foundation-check.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'snippets':len(results),'passed':len(results)}))
