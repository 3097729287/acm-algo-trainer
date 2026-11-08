"""Integer geometry, randomized enclosing circle and offline dominance."""
from nowcoder_editorials import CONTENT,add,read,reviewed_clone
from nowcoder_geometry_support import GEOMETRY,INTEGER

CDQ=r'''
struct Node {int a,b,c,count;long long smaller=0;};
vector<Node> node,buffer;
vector<int> bit;
void update(int p,int value){for(;p<(int)bit.size();p+=p&-p)bit[p]+=value;}
int query(int p){int sum=0;for(;p;p-=p&-p)sum+=bit[p];return sum;}
void solve(int l,int r){
    if(r-l<=1)return;int mid=(l+r)/2;solve(l,mid);solve(mid,r);
    int i=l;for(int j=mid;j<r;j++){while(i<mid && node[i].b<=node[j].b){update(node[i].c,node[i].count);i++;}node[j].smaller+=query(node[j].c);}
    for(int j=l;j<i;j++)update(node[j].c,-node[j].count);
    merge(node.begin()+l,node.begin()+mid,node.begin()+mid,node.begin()+r,buffer.begin()+l,[](const auto &a,const auto &b){return a.b<b.b;});
    copy(buffer.begin()+l,buffer.begin()+r,node.begin()+l);
}
'''
CIRCLE=r'''
struct Circle {Point center;long double radius=-1;};
bool contains(Circle c,Point p){return distance(c.center,p)<=c.radius+1e-12L;}
Circle diameter(Point a,Point b){Point c=(a+b)/2;return {c,distance(a,b)/2};}
Circle throughThree(Point a,Point b,Point c){
    Point u=b-a,v=c-a;long double den=2*cross(u,v);
    if(fabsl(den)<1e-24L){Circle best={{},numeric_limits<long double>::infinity()};for(auto d:{diameter(a,b),diameter(a,c),diameter(b,c)})if(contains(d,a)&&contains(d,b)&&contains(d,c)&&d.radius<best.radius)best=d;return best;}
    Point offset={(dot(u,u)*v.y-dot(v,v)*u.y)/den,(u.x*dot(v,v)-v.x*dot(u,u))/den};
    Point center=a+offset;return {center,distance(center,a)};
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    if 'nowcoder-global::233988' not in existing:
        reviewed_clone(233988,24309,'逐项读过两个原题：均为轴平行矩形并面积，输入n及每矩形两对角，坐标和数量范围可由同一64位扫描线覆盖。',rating=1900)
    put(250561,1500,['Pick定理','鞋带公式','格点计数'],'由格点多边形每一步位移，求内部格点、边界格点与面积。',
        r'从原点依次累加位移，还原顶点。鞋带公式给出二倍面积$S_2=\sum cross(P_i,P_{i+1})$。一条位移$(dx,dy)$的格点边对边界贡献$\gcd(|dx|,|dy|)$，这样每个顶点恰计一次，得边界数$B$。Pick定理$S=I+B/2-1$，所以$I=(S_2-B+2)/2$。全部先用整数计算，最后只按二倍面积奇偶输出.0或.5。',
        r'''int tests;cin >> tests;for(int t=1;t<=tests;t++){int n;cin >> n;long long x=0,y=0,twice=0,boundary=0;for(int i=0;i<n;i++){long long dx,dy;cin >> dx >> dy;twice+=x*dy-y*dx;boundary+=gcd(abs(dx),abs(dy));x+=dx;y+=dy;}twice=abs(twice);cout << "Scenario #" << t << ":\n" << (twice-boundary+2)/2 << ' ' << boundary << ' ' << twice/2 << (twice%2?".5":".0") << "\n\n";}''',
        '边界点数不是各边格点数gcd+1之和，否则每个顶点被重复计算。每组答案后有空行。',complexity=r'时间 $O(n\log C)$，空间 $O(1)$。')
    put(250563,1700,['Pick定理','奇偶性','组合计数'],'全部坐标为偶数时，统计内部格点数为奇数的三角形。',
        r'把三个顶点都除以2，记缩小三角形边界格点数为$b$。原面积为缩小面积的4倍，一定是偶整数；原边界数为$2b$。由Pick定理，原内部点数$I=S-b+1$，故$I$为奇数当且仅当$b$为偶数。'
        '\n\n一条缩小后的边gcd为偶数，当且仅当两个端点的x、y奇偶都相同。把点按(x mod2,y mod2)分4类：三个点全在同类，三条边gcd均偶，满足；恰好两类相同，两条奇边一条偶边，也满足；三个点分别来自三个不同类，三条奇边，不满足。因此答案是C(n,3)减去四种“三类各选一个”的乘积。无需枚举点对。',
        r'''long long n;cin >> n;long long count[4]={};for(int i=0;i<n;i++){long long x,y;cin >> x >> y;count[((x/2)&1)*2+((y/2)&1)]++;}long long answer=n*(n-1)*(n-2)/6;for(int i=0;i<4;i++)for(int j=i+1;j<4;j++)for(int k=j+1;k<4;k++)answer-=count[i]*count[j]*count[k];cout << answer;''',
        '必须先将坐标除以2，再判断奇偶。原坐标本身全偶，直接分类会把所有点放进同一类。',complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(249607,1800,['最近点对','分治','归并排序'],'多组整点，求最近两点距离的平方。',
        '按x排序后分治，左右各求最近距离平方d。归并使区间按y排序，只保留与分界竖线横距平方<d的点。按y遍历条带，倒着比较纵距平方<d的前驱；平面装箱性质保证每个点只需比较常数个候选。递归进入前记住分界x，不能在左右已改为y序后再读取。所有比较都用整数平方，避免开根号误差。'
        '\n\n题面把n下界写成1，而“两个不同点”的任务仅在n≥2时有定义，原题P7883下界为2。代码对n=1保护输出0；有效点对按上述算法处理。',
        r'''int tests;cin >> tests;while(tests--){int n;cin >> n;vector<IPoint> p(n),buffer(n);for(auto &q:p)cin >> q.x >> q.y;sort(p.begin(),p.end(),[](auto a,auto b){return a.x<b.x;});auto squared=[](IPoint a,IPoint b){auto d=a-b;return d.x*d.x+d.y*d.y;};function<long long(int,int)> solve=[&](int l,int r)->long long{if(r-l<=3){long long best=LLONG_MAX;for(int i=l;i<r;i++)for(int j=i+1;j<r;j++)best=min(best,squared(p[i],p[j]));sort(p.begin()+l,p.begin()+r,[](auto a,auto b){return a.y<b.y;});return best;}int mid=(l+r)/2;long long split=p[mid].x,d=min(solve(l,mid),solve(mid,r));merge(p.begin()+l,p.begin()+mid,p.begin()+mid,p.begin()+r,buffer.begin()+l,[](auto a,auto b){return a.y<b.y;});copy(buffer.begin()+l,buffer.begin()+r,p.begin()+l);vector<IPoint> strip;for(int i=l;i<r;i++)if((p[i].x-split)*(p[i].x-split)<d){for(int j=(int)strip.size()-1;j>=0 && (p[i].y-strip[j].y)*(p[i].y-strip[j].y)<d;j--)d=min(d,squared(p[i],strip[j]));strip.push_back(p[i]);}return d;};cout << (n<2?0:solve(0,n)) << '\n';}''',
        '输出距离平方而非距离。坐标差2×10^7，平方和可达8×10^14，用64位。归并保证总复杂度，不在每层重新排序整个条带。',
        declarations=INTEGER,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(243848,1900,['随机增量法','最小覆盖圆'],'求实数点集的最小覆盖圆及圆心。',
        '随机打乱点。依次加入第i点：若已在圆内，当前最优圆无需变化；否则新圆必经过它，先设为半径0的圆。重扫此前点j，若j在圆外，则固定i、j为边界，设为两点直径圆；再重扫k，若k仍在圆外，用i、j、k的外接圆更新。三重循环是边界点逐层固定，不是枚举全部三元组；随机顺序下期望线性。三点共线时取能包含三点的最远点对直径圆。',
        r'''int n;cin >> n;vector<Point> p(n);for(auto &q:p)cin >> q.x >> q.y;mt19937 engine(712367821);shuffle(p.begin(),p.end(),engine);Circle circle;for(int i=0;i<n;i++)if(!contains(circle,p[i])){circle={p[i],0};for(int j=0;j<i;j++)if(!contains(circle,p[j])){circle=diameter(p[i],p[j]);for(int k=0;k<j;k++)if(!contains(circle,p[k]))circle=throughThree(p[i],p[j],p[k]);}}cout << fixed << setprecision(15) << circle.radius << '\n' << circle.center.x << ' ' << circle.center.y;''',
        '内部计算使用long double，输出15位小数。避免用普通double配过大的EPS，否则1e−9精度要求可能失守。',
        declarations=GEOMETRY+CIRCLE,floating_output=True,complexity=r'随机顺序下期望 $O(n)$，最坏 $O(n^3)$；空间 $O(n)$。')
    put(243846,1900,['CDQ分治','树状数组','三维偏序'],'统计每个点被多少其他点三维同时不大于，并输出频数分布。',
        '先按(a,b,c)字典序排序，把完全相同的点合成一个带count的点。CDQ按此顺序分左右，左组a不会大于右组；递归后两组各按b排序，扫右点时把所有左组b≤当前b的count加入c上的树状数组，查c前缀即跨组贡献。回滚本轮加入后，按b归并。一个合并点最终答案=跨组smaller+自身count−1，频数桶增加count。'
        '\n\n相同a也可计入：字典序下，若两个不同合并点可互相满足偏序，必然b、c也相同，早已被合并；否则只有排在前面的点可能支配后面的点。',
        r'''int n,k;cin >> n >> k;vector<array<int,3>> p(n);for(auto &q:p)cin >> q[0] >> q[1] >> q[2];sort(p.begin(),p.end());for(auto q:p){if(!node.empty() && node.back().a==q[0] && node.back().b==q[1] && node.back().c==q[2])node.back().count++;else node.push_back({q[0],q[1],q[2],1,0});}buffer.resize(node.size());bit.resize(k+1);solve(0,node.size());vector<int> answer(n);for(auto q:node)answer[q.smaller+q.count-1]+=q.count;for(int x:answer)cout << x << '\n';''',
        '≤条件含等号，扫b时不能写成<。必须合并完全重复三元组，不然同组重复点的贡献会随输入顺序丢失。',
        declarations=CDQ,complexity=r'时间 $O(n\log n\log k)$，空间 $O(n+k)$。')
    put(231085,2200,['支撑函数','凸包','三角函数化简'],'判断每个函数能否在某个自变量处严格小于其他所有函数。',
        r'反正切在非负数上单调。把比较量$k_i/|\cos(x-a_i)|$取倒数，等价于让$|\cos(x-a_i)|/k_i$严格最大。展开余弦，令$v_i=(\cos a_i/k_i,\sin a_i/k_i)$、$u=(\cos x,\sin x)$，就是最大化$|u\cdot v_i|=\max(u\cdot v_i,u\cdot(-v_i))$。'
        '\n\n因此构造所有±v_i的凸包。某个函数能够严格胜出，当且仅当它的一个点是严格凸包顶点，且该坐标没有另一个函数重复：顶点有一段非空外法向角域使它唯一取最大；边内点与内部点均不能唯一最大。a的单位为弧度，直接计算sin/cos，不转成度。删除共线中间点，最终标记保留下来的顶点所属函数。',
        r'''int n;cin >> n;struct Vertex{long double x,y;int id;};vector<Vertex> p;for(int i=0;i<n;i++){long double k,a;cin >> k >> a;long double x=cosl(a)/k,y=sinl(a)/k;p.push_back({x,y,i});p.push_back({-x,-y,i});}sort(p.begin(),p.end(),[](auto a,auto b){return a.x!=b.x?a.x<b.x:a.y<b.y;});auto turn=[](Vertex a,Vertex b,Vertex c){return (b.x-a.x)*(c.y-b.y)-(b.y-a.y)*(c.x-b.x);};vector<Vertex> hull;for(auto q:p){while(hull.size()>=2 && turn(hull[hull.size()-2],hull.back(),q)<=0)hull.pop_back();hull.push_back(q);}int lower=hull.size();for(int i=(int)p.size()-2;i>=0;i--){while((int)hull.size()>lower && turn(hull[hull.size()-2],hull.back(),p[i])<=0)hull.pop_back();hull.push_back(p[i]);}if(hull.size()>1)hull.pop_back();string answer(n,'0');for(auto q:hull)answer[q.id]='1';cout << answer;''',
        '输入保证(k,a)不重复，a为整数弧度；非零整数不可能恰为π的整数倍，故不同函数不会产生完全相同的±v。用long double计算，不设过大绝对EPS去吞掉小半径凸包转角。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(232792,2300,['旋转扫描线','三角形面积','凸包'],'求任取三点的不信任度最小值和最大值，即二倍三角形面积。',
        '不信任度是两条边向量行列式的绝对值，等于二倍三角形面积，最后不再除2。最大值只需在凸包上找；固定第一个顶点，第二个顶点前进时，第三个顶点的最大面积位置也单调前进，得到O(h²)。'
        '\n\n最小值不能只看一个原点极角相邻的点。考虑旋转一条投影法线，维护所有点的投影顺序：两个点A、B投影相同时，扫描方向平行AB，两点交换次序。此时距离AB直线最近的第三点，只可能是这对相邻点在顺序外的两个邻居。把所有点对方向归一到[0,π)，按叉积排序，依次检查两个外邻居并交换两端；所有三角形的某条底边都会作为事件出现，因此覆盖最小值。'
        '\n\n初始顺序是y升序、同y时x升序，对应角度0稍前。若事件端点不相邻，说明两点之间有第三点投影相等，即三点共线，最小值立即为0；邻居叉积为0同理。平行但不共线的点对交换互不影响。重复点也直接得到最小值0。点对事件用两个16位编号减少内存，方向用32位，面积用128位。',
        r'''int n;cin >> n;vector<IPoint> p(n);for(auto &q:p)cin >> q.x;for(auto &q:p)cin >> q.y;auto hull=integerHull(p);Wide maximum=0;int h=hull.size();for(int i=0;i<h;i++){int k=i+2;for(int j=i+1;j+1<h;j++){k=max(k,j+1);auto area=[&](int z){return cross(hull[j]-hull[i],hull[z]-hull[i]);};while(k+1<h && area(k+1)>area(k))k++;maximum=max(maximum,area(k));}}vector<int> order(n),position(n);iota(order.begin(),order.end(),0);sort(order.begin(),order.end(),[&](int a,int b){return p[a].y!=p[b].y?p[a].y<p[b].y:p[a].x<p[b].x;});bool duplicate=false;for(int i=0;i<n;i++){position[order[i]]=i;if(i && p[order[i]].x==p[order[i-1]].x && p[order[i]].y==p[order[i-1]].y)duplicate=true;}Wide minimum=maximum;if(!duplicate && minimum){struct Event {int dx,dy;uint16_t u,v;};vector<Event> events;events.reserve((long long)n*(n-1)/2);for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){IPoint d=p[j]-p[i];if(d.y<0 || (d.y==0 && d.x<0)){d.x=-d.x;d.y=-d.y;}events.push_back({(int)d.x,(int)d.y,(uint16_t)i,(uint16_t)j});}sort(events.begin(),events.end(),[](const Event &a,const Event &b){long long c=(long long)a.dx*b.dy-(long long)a.dy*b.dx;if(c)return c>0;return a.u!=b.u?a.u<b.u:a.v<b.v;});for(auto e:events){int u=position[e.u],v=position[e.v];if(u>v)swap(u,v);if(v-u!=1){minimum=0;break;}for(int at:{u-1,v+1})if(at>=0 && at<n)minimum=min(minimum,absolute(cross(p[e.v]-p[e.u],p[order[at]]-p[e.u])));if(!minimum)break;swap(order[u],order[v]);position[order[u]]=u;position[order[v]]=v;}}else if(duplicate)minimum=0;printWide(minimum);cout << '\n';printWide(maximum);''',
        '点对方向归一后都位于同一个半平面，叉积排序才有严格顺序。不能用atan2相等判三点共线，也不能用随机抽样代替最小值证明。',
        declarations=INTEGER,complexity=r'时间 $O(n^2\log n)$，空间 $O(n^2)$；事件12字节，n=3000时约54MB。')


if __name__=='__main__':run()
