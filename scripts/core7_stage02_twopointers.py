"""Explicit route methods for the two-pointer unit, preserving its old program."""
import json
import re
from core7_authoring import add,SPECS,CONTENT

A=['io-basics','basic-control','vector','integer']
S=A+['sort','iterators']

retained=json.loads((CONTENT/'P12342/retained-existing.json').read_text('utf-8'))
old_programs=[re.findall(r'^```cpp\s*\n(.*?)^```',retained[v]['markdown'],re.M|re.S) for v in ['default','detailed']]
assert len(old_programs[0])==1 and old_programs[0]==old_programs[1]
add('P12342','排序后贪心匹配所有无需修改的数',
    'B 可以任意重排，也可先把某些值改为任意整数，求让每个 a−b 都严格为正的最少修改次数。',
    r'''先让尽量多的原 B 值匹配到严格更大的 A。两数组排序，依次看从小到大的 a，若最小未用 b<a 就匹配，否则这个 a 无法匹配任何剩余 b，跳过。最大匹配数为 used，答案 n−used，剩余 B 可改成足够小的整数。''',
    r'''样例排序后 A 为 [12,14,22,31]，B 为 [3,19,27,44]。三可匹配十二，十九匹配二十二，二十七匹配三十一，四十四没有更大的 A，改一次即可。原 A 不允许重排并不妨碍求值：排序只用于找匹配，最终把每个匹配的 B 放回对应 A 的原位置即可。

固定当前最小的未匹配 A。若最小未用 B 都不小于它，所有其它 B 只会更大，这个 A 不可能保留某个未修改的 B，跳过不会损失匹配。若最小 B 严格小于它，就把两者配上：任何最优匹配若使用了更大的 B，可交换，让更小的 B 来服务当前 A，把原搭档留给后面更大的 A，不会破坏合法性；若当前 A 原本未匹配，也可用此配对替换 B 的原匹配或直接增加一对。因此存在最优解遵循当前贪心，之后继续处理剩余问题。

最多保留 used 个原值，至少有 n−used 个 B 必须改。反过来，把未匹配 B 都改成比所有 A 更小的整数，再分配给剩余 A，就能用 n−used 次完成；题目允许改成任意整数，不受原输入范围限制。因此下界可达到。

比较必须严格小于，a=b 的差为零，不能保留。负数没有特殊处理，排序和同样的不等式仍成立。参考程序保留已有验证版本，不改其源码。''',
    '',
    'B 可以重排，A 的排序只是匹配计算；相等不合法；未匹配值可直接改为足够小。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['排序','贪心','双指针'],lessons=S+['greedy','two-pointers'],
    key=retained['methodCatalog'].get('primaryMethod','direct'))
SPECS[-1].code=old_programs[0][0]
SPECS[-1].images={**retained['default']['images'],**retained['detailed']['images']}

add('CF1237B','维护最早尚未出洞的入口车',
    '已知每辆车进入和离开隧道的顺序，超越过至少一辆更早进入的车就罚一次，求被罚的车数。',
    r'''用指针指向入口顺序中最早尚未离开的车，另记每辆车是否已出洞。扫描出口车 x，先跳过入口指针处已经离开的车；若 x 不是指针所指车，就说明有更早进洞的车还没出来，x 必被罚一次。之后标记 x 已出洞。''',
    r'''入口 [3,5,2,1,4]，第一辆出来的是四，但更早进入的三还在里面，所以四超车、罚一次。随后三正常出来，指针来到五；二却先于五出来，因此二也罚一次。五出来后，指针会跳过已经出来的二，再来到一。

扫描出口时，入口指针指向所有尚未离开者中进洞最早的一辆。若当前 x 就是它，则不存在更早进入仍未离开的车，x 没有形成题目定义的超车。若不是它，指针那辆车比 x 更早进入、却会比 x 更晚离开，就是一个确定被 x 超越的对象，因此 x 应罚。

每辆出口车只判断一次，哪怕它超越多辆也只加一次，不统计全部逆序对。已经被后车提前超越而出洞的车辆，未来必须被入口指针跳过，不能反复拿它们当作还在洞内的障碍。指针总共走 n 次，整体线性。''',
    r'''int n;cin>>n;vector<int>entered(n);for(int &x:entered)cin>>x;vector<bool>left(n+1);int next=0,answer=0;
// 当前最早仍在洞内的车，决定出口车有没有超车。
for(int i=0;i<n;++i){int x;cin>>x;while(next<n&&left[entered[next]])++next;
    if(entered[next]!=x)++answer;left[x]=true;
}
cout<<answer<<'\n';''',
    '罚的是超车者，每车最多一次；指针必须跳过此前已经离开的车。',
    '时间、空间均为 $O(n)$。',tags=['双指针','模拟'],lessons=A+['arrays','two-pointers'])

add('CF1304C','维护全部可达温度区间，先扩张再相交',
    '空调每分钟可升温一、降温一或保持，给定按时间排序的预约温度范围，判断能否满足全部预约。',
    r'''当前可达温度是闭区间 [low,high]。到下一预约经过 dt 分钟，先扩张为 [low−dt,high+dt]，再与客户范围相交。交集非空继续，空则不可能。初始区间是单点初温。''',
    r'''若上一预约后可处于二到四度，三分钟后可达到负一到七度中的任意整数；下一位要求五到六度，便把可达区间缩成 [5,6]。只保留某个随意选择的当前温度会过早丢掉其它可行方案。

从区间内任意温度出发，dt 分钟内最多变 dt，也可关机保持或在整数分钟切换，故所有可达整数恰好覆盖 [low−dt,high+dt]。再满足当时客户的闭区间要求，就取两区间交集：low=max(low−dt,l)，high=min(high+dt,h)。交集为连续区间，状态仍只需两个端点。

这个状态同时保留所有满足此前预约的可能性，因此每轮相交为空，等价于此前任何合法温度轨迹都无法满足当前要求；交集非空则每个保留值都有某条此前轨迹可以延伸到它，不会只是在端点上空想。

相同时间的客户之间 dt=0，必须满足他们范围的交集，不能多获得一分钟。即使某组已判无解，也要继续读完其余预约，避免下一组输入错位。端点扩张可超出原温度输入范围，使用 long long。''',
    r'''int tests;cin>>tests;while(tests--){int n;long long initial;cin>>n>>initial;long long low=initial,high=initial,time=0;bool possible=true;
    for(int i=0;i<n;++i){long long t,l,h;cin>>t>>l>>h;long long elapsed=t-time;
        // 时间经过先扩张可达范围，再与预约求交。
        if(possible){low=max(low-elapsed,l);high=min(high+elapsed,h);if(low>high)possible=false;}time=t;
    }
    cout<<(possible?"YES":"NO")<<'\n';
}''',
    '范围包含端点；相同预约时刻不增加移动时间；判无解后仍需读完输入。',
    '每组时间 $O(n)$、额外空间 $O(1)$。',tags=['贪心'],lessons=A+['greedy','coordinates'])

add('CF1148B','枚举两程取消名额的分配',
    '乘客选最快可行的两段航班，你最多取消 k 班来尽量拖延；若能让他完全到不了，输出负一。',
    r'''枚举取消第一程最早 x 班，首个可乘为 a[x]。到达中转站后 lower_bound 找第二程首个不早于到达的航班 j，再取消其中最早 k−x 班，最终乘 j+k−x。越界即可阻断，否则对所有 x 取最终到达时间最大值。''',
    r'''取消名额必须在两程间分配，不能只把第一程尽量推后。样例一最优是取消第一程一班，再取消中转后最早可接的一班，使最终到达十一。

固定第一程最早剩余航班为 a[x]，就必须取消它之前 x 班。其它第一程取消对最早可出发者没有作用，不如留给第二程。乘客到中转站时刻是 a[x]+ta，所有早于它的第二程航班本来就赶不上，也无需取消。剩余名额应顺次取消从 lower_bound 得到的首个可接航班起的 k−x 班，乘客最终只能选到后面的位置 j+k−x。

更晚出发第一程不可能更早到达中转，也不会遇到更早的第二程可乘班次，因此乘客总可选择最早剩余第一程；我们只需上述有限种名额分配。若某个分配让第二程下标越界，说明可以取消到全程无路，按要求立即输出 −1。第一程或第二程总班数本身不超过 k 时，更可直接全部取消。

衔接允许到达时刻等于起飞时刻，使用 lower_bound 而不是 upper_bound。原输入两列起飞时刻已各自升序，无须改变航班顺序。最终时刻可以超过十亿，用 long long。''',
    r'''int n,m,k;long long ta,tb;cin>>n>>m>>ta>>tb>>k;vector<long long>a(n),b(m);for(auto &x:a)cin>>x;for(auto &x:b)cin>>x;
if(k>=n||k>=m){cout<<-1<<'\n';return 0;}long long answer=0;
// x 个取消名额给第一程，其余给中转后最早可接的航班。
for(int x=0;x<=k;++x){int first=(int)(lower_bound(b.begin(),b.end(),a[x]+ta)-b.begin());int selected=first+k-x;
    if(selected>=m){cout<<-1<<'\n';return 0;}answer=max(answer,b[selected]+tb);
}
cout<<answer<<'\n';''',
    '下标从零，取消 x 班后首班为 a[x]；衔接等号合法；发现可阻断方案直接输出 −1。',
    r'时间 $O(n+m+(k+1)\log(m+1))$、空间 $O(n+m)$。',tags=['枚举','二分查找','贪心'],lessons=A+['bounds','enumeration','greedy','iterators'])

add('CF644B','队列保存全部未完成任务的完成时刻',
    '单线程服务器按到达顺序处理任务，另有 b 个等待位，等待满时拒绝新任务，输出每个任务的完成时刻或负一。',
    r'''队列保存正在处理及等待的所有已接收任务的完成时刻。新任务到达时，先弹出完成时间≤到达时刻的任务；若剩余数已经大于 b，则正在处理加等待共 b+1 个，拒绝。否则新完成时刻为 max(到达时刻,队尾完成时刻)+耗时，并入队。''',
    r'''等待队列容量 b 不包括正在执行的任务。因此 b=1 时，可以同时存在一个正在执行、一个等待，共两个未完成任务，第三个才会拒绝。把保存所有未完成任务的队列直接限制为 b，会少接一个。

队列中的完成时刻严格递增，因为任务耗时为正，按先到先服务依次开工。新任务到达 t 时，把所有完成时间≤t 的队首都删掉；题目明确同刻完成与接手先发生，新到达后发生，所以等号也要弹出。

队列非空时，最后一个已接收任务完成后新任务才能开始，故完成时刻为 queue.back()+duration；队列为空时服务器可能已经空闲，必须从当前 t 开始，不能从过去的旧结束时刻开始。统一写 max(t,last_finish)+duration。

若剩余队列长度为 b+1，说明一项运行、b 项等待，拒绝后任何队列状态都不改变。每个接收任务只入队、出队一次，拒绝任务从未入队，总时间线性。完成时间可累加到远大于输入时刻，使用 long long。''',
    r'''int n,b;cin>>n>>b;deque<long long>finish;vector<long long>answer;
for(int i=0;i<n;++i){long long t,d;cin>>t>>d;while(!finish.empty()&&finish.front()<=t)finish.pop_front();
    // b 是等待位；另有一项可以正在执行。
    if((int)finish.size()>b){answer.push_back(-1);continue;}
    long long end=max(t,finish.empty()?t:finish.back())+d;finish.push_back(end);answer.push_back(end);
}
for(int i=0;i<n;++i)cout<<answer[i]<<(i+1==n?'\n':' ');''',
    '等待位不含运行中的任务；相同时间先处理完成事件；拒绝任务不改变队列。',
    '时间、空间均为 $O(n)$。',tags=['队列','模拟'],lessons=A+['queue-stack'])
