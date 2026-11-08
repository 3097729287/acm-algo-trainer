"""Repair five iframe-PDF rows previously mis-imported as loading placeholders.

The readable text is an original Chinese restatement of verified technical facts.
The linked source PDFs and their byte hashes remain in the provenance.
"""
import copy
import json
import sys

from nowcoder_editorials import BASELINE, CONTENT, OUT, ROOT, add, database, read, reviewed_clone, sha, statement, write

sys.path.insert(0,str(ROOT / 'backend'))
from statement_seed import checksum, load_statements


def run():
    sources = read(OUT / 'pdf-sources.json')
    restatements = {
        116634: (251558, '按顺序到来n个人，每个人有两个越小越好的评分。若另一人两项均不劣且至少一项严格更好，则此人被支配。每次加入后，输出当前不被任何已到来者支配的人数，完全同分者互不支配。',
                 '首行测试组数T，1≤T<40。每组先给n（0≤n≤15000），再给n行两项评分，均在0到10^9。',
                 '每组先输出Case #x:，随后n行各输出一次人数，测试组之间空一行。'),
        117187: (251580, '湖泊是r行c列网格，每格给一个0到7的洋流方向，依次为北、东北、东、东南、南、西南、西、西北。船可向八邻格移动，顺出发格洋流耗能0，选其他方向耗能1，不能越界。对每次起终点询问求最小总能量。',
                 '先给r、c，均不超过1000，再给r行方向数字。之后给至多50次询问，每次给起点行列和终点行列，编号从1开始。',
                 '每次询问一行最小能量。'),
        124063: (251572, '我方n支部队和敌方m个村落各有攻击力、防御力。每支我军至多出战一次，每个敌村至多受一支我军攻击。双方同时攻击，防御力不大于对方攻击力的一方阵亡。必须消灭全部敌军，最大化我方战后存活总数，包括未出战部队。',
                 '首行T（1≤T≤100）。每组先给n、m，各不超过10^5，接着n行我军、m行敌军，每行先攻击、后防御，数值为1到10^9。',
                 '每组输出Case #x: y，y为最多存活数；不能消灭全部敌军时为-1。'),
        124167: (251589, '有n个地点，若两点同属第i个集合，就能以t_i分钟从其中任一点到另一个点。两位朋友分别从1号、n号地点同时出发，可等待，求最早会合时间以及全部最优会合地点。会合只能发生在原地点。',
                 '首行T（1≤T≤6）。每组给n、m，2≤n≤10^5；接着m行先给t_i、集合大小S_i，再列出成员地点。1≤t_i≤10^9，所有S_i之和不超过10^6。',
                 '按样例输出Case #x: time，下一行升序列出全部最优地点；无法会合时输出Case #x: Evil John。'),
        124160: (None, 'm块石头围成环，编号0到m-1。n只青蛙都从0出发，第i只每步从j跳到(j+a_i) mod m，可跳任意多步。被任何青蛙到过的石头都算占据，即使青蛙后来离开也仍计入。求所有被占据石头的编号之和。',
                 '首行T，不超过20。每组先给n、m（1≤n≤10^4，1≤m≤10^9），再给n个步长a_i（1≤a_i≤10^9）。',
                 '每组输出Case #x: sum，x从1开始，sum为被占据编号总和。'),
    }
    db = database()
    patches = []
    for number, (counterpart, description, input_text, output_text) in restatements.items():
        identity = f'nowcoder-global::{number}'
        old = json.loads(db.execute('SELECT content FROM statements WHERE problem_id=?',(identity,)).fetchone()[0])
        assert '列表加载中' in old['markdown'] and not old['samples']
        value = copy.deepcopy(old)
        pdf = sources[str(number)]['pdf']
        if counterpart:
            samples = copy.deepcopy(statement(f'nowcoder-global::{counterpart}')['samples'])
        else:
            samples = [{'name':'样例 1','input':'3\n2 12\n9 10\n3 60\n22 33 66\n9 96\n81 40 48 32 64 16 96 42 72',
                        'output':'Case #1: 42\nCase #2: 1170\nCase #3: 1872'}]
        value.update(markdown=f'# {old["title"]}\n\n## 题目描述\n\n{description}\n\n## 输入描述\n\n{input_text}\n\n## 输出描述\n\n{output_text}\n\n[原始PDF题面]({pdf})',
                     samples=samples, statementVersion=old['statementVersion'] + 1,
                     integrity={'schema':1,'sourceVerified':True,'status':'complete','sampleCount':len(samples),
                                'pdfPageCountVerified':True,'pdfPageCount':1,'checkedAt':'2026-11-08'},
                     sourcePdfUrl=pdf,sourcePdfSha256=sha((OUT / f'{number}.pdf').read_bytes()),
                     sourceRepair={'reason':'Original iframe PDF was missed and a loading-menu placeholder was imported.',
                                   'beforeMarkdownSha256':sha(old['markdown']),'restatementLanguage':'zh-CN'})
        write(CONTENT / 'statements' / f'NC{number}.json',value)
        patches.append({'problem_id':identity,'beforeSha256':checksum(old),'content':value})
    db.close()
    packet = ROOT / 'data/library/statement-patches/zzzzzzzzz-nowcoder-editorials-pdf-20261108.json'
    write(packet,{'schema':1,'statements':patches})
    resolved = {row['problem_id']:row['content'] for row in load_statements(ROOT / 'data/library')}
    assert all(resolved[patch['problem_id']] == patch['content'] for patch in patches)
    ledger = read(CONTENT / 'reviewed.json')
    for number, (counterpart, *_) in restatements.items():
        if counterpart and f'nowcoder-global::{number}' not in ledger:
            reviewed_clone(number,counterpart,'已逐页读取并核对牛客原页内嵌PDF；规则、接口及原PDF样例均与此已验证题一致。原页面的“列表加载中”占位题面已用经过核对的中文事实转述修复，并保留原PDF链接与文件SHA256。')
    if 'nowcoder-global::124160' not in ledger:
        add(124160,2100,['最大公约数','欧拉函数','因数枚举'], '多只青蛙从0按各自固定步长绕环，求所有可到石头编号之和。',
            '步长a的青蛙能到的恰是gcd(a,m)的倍数。所有这些g都整除m，先去重。对于任意石头x，令d=gcd(x,m)，它被覆盖当且仅当某个g整除d。因此可以按m的因数d分组，只需检查因数之间的整除。\n\n当d<m时，gcd(x,m)=d的非零石头有phi(m/d)个，这是把x除以d后的互质剩余类。累加所有被覆盖组的人数count。覆盖集合在x与m−x之间成对对称，每对编号和为m，所以编号总和为m*count/2；0不影响总和，单独排除d=m即可。m/2若是自对称点，m一定为偶数，公式仍是整数。分解m一次就能算各组欧拉函数。',
            r'''int tests; cin >> tests; for (int tc = 1; tc <= tests; tc++) { int n; long long m; cin >> n >> m; set<long long> groups; for (int i = 0; i < n; i++) { long long a; cin >> a; groups.insert(gcd(a,m)); } vector<long long> divisors, primes; for (long long d = 1; d * d <= m; d++) if (m % d == 0) { divisors.push_back(d); if (d * d != m) divisors.push_back(m / d); } long long remaining = m; for (long long p = 2; p * p <= remaining; p++) if (remaining % p == 0) { primes.push_back(p); while (remaining % p == 0) remaining /= p; } if (remaining > 1) primes.push_back(remaining); long long count = 0; for (long long d : divisors) if (d < m) { bool covered = false; for (long long g : groups) if (d % g == 0) { covered = true; break; } if (!covered) continue; long long q = m / d, phi = q; for (long long p : primes) if (q % p == 0) phi = phi / p * (p - 1); count += phi; } cout << "Case #" << tc << ": " << m * count / 2 << '\n'; }''',
            '不是把所有步长一起取一个gcd：不同青蛙的可达集合取并集，不是允许在途中任意切换步长。编号范围是0到m−1，不含m。答案和乘积使用64位。',
            complexity=r'因数数 $D$、不同gcd数 $G\le D$，时间 $O(n\log m+\sqrt m+DG+D\omega(m))$，空间 $O(D+G)$。',
            cases=[{'input':'2\n1 1\n1\n2 6\n2 3','output':'Case #1: 0\nCase #2: 9'}])
    print('Repaired and authored five verified PDF-backed tasks.')


if __name__ == '__main__':
    run()
