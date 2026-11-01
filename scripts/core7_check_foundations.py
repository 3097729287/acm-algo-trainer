"""Compile and execute the new language examples with explicit expected results."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import contextlib
from core7_authoring import ROOT,OUT

checks={
    'monotone-structures': [('', '3 3 0\n4 6\n','for(int n=1;n<=6;++n){int states=1;for(int i=0;i<n;++i)states*=4;for(int code=0;code<states;++code){vector<long long>x(n);int value=code;for(auto &v:x){v=value%4;value/=4;}auto next=nextGreater(x);for(int i=0;i<n;++i){int expected=0;for(int j=i+1;j<n;++j)if(x[j]>x[i]){expected=j+1;break;}assert(next[i]==expected);}for(int k=1;k<=n;++k){auto actual=slidingMaximum(x,k);for(int i=0;i+k<=n;++i){long long expected=x[i];for(int j=i;j<i+k;++j)expected=max(expected,x[j]);assert(actual[i]==expected);}}}}')],
    'monotone-contribution': [('', '13\n','assert(sumMinimums({})==0);for(int n=1;n<=6;++n){int states=1;for(int i=0;i<n;++i)states*=4;for(int code=0;code<states;++code){vector<long long>x(n);int value=code;for(auto &v:x){v=value%4;value/=4;}long long expected=0;for(int l=0;l<n;++l)for(int r=l;r<n;++r){long long smallest=x[l];for(int j=l;j<=r;++j)smallest=min(smallest,x[j]);expected+=smallest;}assert(sumMinimums(x)==expected);}}')],
    'digit-dp': [('10\n','7\n','long long brute=0;assert(countWithout11(0)==0);for(int x=1;x<=1000;++x){brute+=(x&(x>>1))==0;assert(countWithout11(x)==brute);}')],
    'digit-aggregation': [('', '2 36 9\n','assert(count==2&&nextNumeric==13+23&&nextDigits==1+3+2+3);')],
    'linear-recurrence': [('12\n','144\n','vector<long long>zero(20);assert(term(zero,recurrence(zero),1000000000000LL)==0);mt19937 random(20261031);for(int degree=1;degree<=8;++degree)for(int test=0;test<6;++test){vector<long long>coefficient(degree),known(150);for(auto &x:coefficient)x=random()%21;for(int i=0;i<degree;++i)known[i]=random()%21;for(int i=degree;i<150;++i)for(int j=1;j<=degree;++j)known[i]=(known[i]+coefficient[j-1]*known[i-j])%MOD;vector<long long>initial(known.begin(),known.begin()+2*degree);auto recovered=recurrence(initial);assert(recovered.size()<=size_t(degree));for(int i:{0,1,2*degree-1,2*degree,50,149})assert(term(initial,recovered,i)==known[i]);}')],
    'bitset-states': [('', '1 1 1 3\n', ''),('', '2 1\n','')],
    'subset-enumeration': [('', '22 20 18 16 6 4 2 0 \n2 27\n', 'assert(subsets==vector<unsigned>({22,20,18,16,6,4,2,0}));')],
    'decimal-signed': [('', '1\n1234567890123456789000000000\n1\n', 'assert(!Number("-000").negative);assert(plusNumber(Number("-8"),Number("12")).digits=="4");assert(plusNumber(Number("-8"),Number("5")).negative);assert(plusNumber(Number("-8"),Number("5")).digits=="3");assert(plusNumber(Number("-123"),Number("123")).digits=="0");')],
    'standard-array': [('', '4 5 1\n', 'assert((saved==array<int,4>{2,3,0,0}));assert((counts==array<int,4>{1,1,1,1}));')],
    'rectangle-prefix': [('', '17\n', 'assert(p[3][4]==33&&p[1][4]==10&&p[3][1]==8&&p[1][1]==2); for(int x1=0;x1<=n;++x1)for(int x2=x1;x2<=n;++x2)for(int y1=0;y1<=m;++y1)for(int y2=y1;y2<=m;++y2){long long direct=0;for(int x=x1;x<x2;++x)for(int y=y1;y<y2;++y)direct+=a[x][y];assert(direct==p[x2][y2]-p[x1][y2]-p[x2][y1]+p[x1][y1]);}')],
    'lambda-local': [('', '', 'assert(answer==5);'),
               ('', '', 'assert(a);threshold=20;assert(enough(12));'),
               ('', '', 'assert(a==11&&b==21);auto next=[base]() mutable {return ++base;};assert(next()==21&&next()==22&&base==20);'),
               ('', '', 'assert((items==vector<pair<int,int>>({{1,4},{1,2},{2,7}})));'),
               ('', '', 'assert(value==120);')],
    'weighted-dsu': [('', '2 1 0\n', '')],
    'subtree-regions': [('', '11 1 2 1 ', 'assert(parent==vector<int>({-1,0,0,2}));assert(mass==vector<unsigned long long>({11,1,2,1}));')],
    'vector-ranges': [('', '', 'assert(first_value==2);assert(snapshot==vector<int>({0,2,3,4}));assert(result==source&&source==vector<int>({1,2,3,4,5}));')],
    'order-selection': [('', '', 'assert(smallest_sum==6);assert(values[3]==5);for(int i=0;i<3;++i)assert(values[i]<=values[3]);')],
    'interactive-io': [('7\n','? 1 3\n! 7\n','')],
    'rectangle-difference': [('', '', 'assert(covered==6);assert(diff[1][1]==1&&diff[2][3]==1&&diff[3][3]==0&&diff[0][1]==0);')],
    'prime-sieve': [('', '', 'assert(primes==vector<int>({2,3,5,7,11,13,17,19,23,29}));assert(!is_prime[0]&&!is_prime[1]&&!is_prime[25]);')],
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
with contextlib.nullcontext(tempfile.mkdtemp(prefix='core7-language-',dir=OUT)) as temporary:
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
