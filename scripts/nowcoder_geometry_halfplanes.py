"""Convex inset, strict depth and two offline geometric counting templates."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_geometry_support import GEOMETRY

HPI=r'''
struct Line {Point p,d;long double angle;};
Line line(Point a,Point b){Point d=(b-a)/distance(a,b);return {a,d,atan2l(d.y,d.x)};}
bool left(const Line &l,Point p){return cross(l.d,p-l.p)>=-1e-15L;}
Point intersection(const Line &a,const Line &b){return a.p+a.d*(cross(b.p-a.p,b.d)/cross(a.d,b.d));}
vector<Point> halfplanes(vector<Line> input){
    const long double box=1e9L;
    vector<Point> corners={{-box,-box},{box,-box},{box,box},{-box,box}};
    for(int i=0;i<4;i++)input.push_back(line(corners[i],corners[(i+1)%4]));
    sort(input.begin(),input.end(),[](const Line &a,const Line &b){return a.angle<b.angle;});
    vector<Line> unique;
    for(auto l:input){if(!unique.empty() && fabsl(cross(unique.back().d,l.d))<1e-18L && dot(unique.back().d,l.d)>0){if(cross(unique.back().d,l.p-unique.back().p)>0)unique.back()=l;}else unique.push_back(l);}
    deque<Line> q;
    for(auto l:unique){
        while(q.size()>1 && !left(l,intersection(q[q.size()-2],q.back())))q.pop_back();
        while(q.size()>1 && !left(l,intersection(q[0],q[1])))q.pop_front();
        if(!q.empty() && fabsl(cross(q.back().d,l.d))<1e-18L)return {};
        q.push_back(l);
    }
    while(q.size()>2 && !left(q.front(),intersection(q[q.size()-2],q.back())))q.pop_back();
    while(q.size()>2 && !left(q.back(),intersection(q[0],q[1])))q.pop_front();
    if(q.size()<3 || fabsl(cross(q.front().d,q.back().d))<1e-18L)return {};
    vector<Point> result;for(int i=0;i<(int)q.size();i++)result.push_back(intersection(q[i],q[(i+1)%q.size()]));return result;
}
long double polygonArea(const vector<Point> &p){long double sum=0;for(int i=0;i<(int)p.size();i++)sum+=cross(p[i],p[(i+1)%p.size()]);return fabsl(sum)/2;}
'''
TIME_CDQ=r'''
struct Event {long long x,y;int kind,id,rank;};
vector<Event> event,buffer;
vector<long long> bit,answer;
const long long NEG=-(1LL<<60);
void add(int p,long long value){for(;p<(int)bit.size();p+=p&-p)bit[p]=max(bit[p],value);}
long long maximum(int p){long long value=NEG;for(;p;p-=p&-p)value=max(value,bit[p]);return value;}
void cdq(int l,int r){
    if(r-l<=1)return;int mid=(l+r)/2;cdq(l,mid);cdq(mid,r);
    int i=l;
    for(int j=mid;j<r;j++){while(i<mid && event[i].x<=event[j].x){if(event[i].kind==1)add(event[i].rank,event[i].x+event[i].y);i++;}if(event[j].kind==2){long long best=maximum(event[j].rank);if(best!=NEG)answer[event[j].id]=min(answer[event[j].id],event[j].x+event[j].y-best);}}
    for(int j=l;j<i;j++)if(event[j].kind==1)for(int p=event[j].rank;p<(int)bit.size();p+=p&-p)bit[p]=NEG;
    merge(event.begin()+l,event.begin()+mid,event.begin()+mid,event.begin()+r,buffer.begin()+l,[](const Event &a,const Event &b){return a.x<b.x;});
    copy(buffer.begin()+l,buffer.begin()+r,event.begin()+l);
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(233170,2000,['半平面交','二分答案','最大内切圆'],'求凸多边形内距离海岸最远的点到边界的距离。',
        '答案是最大内切圆半径。检验半径r时，圆心必须在每条逆时针边左侧，且到边所在直线距离至少r；把每条边沿单位左法向量向内平移r，求这些左半平面的交。交非空就可放置该圆，随着r增加可行域只会缩小，二分60轮足以达到1e−5精度。'
        '\n\n半平面交将直线按方向角排序，同向线只保留更靠内的一条，用双端队列维护相邻交点：新约束不包含队尾或队首交点时弹出对应线，最后收尾闭合。代码加入远大于输入范围的辅助方框，统一处理过程中的无界交；它不改变本题有界答案。',
        r'''int n;while(cin >> n && n){vector<Point> p(n);for(auto &q:p)cin >> q.x >> q.y;auto feasible=[&](long double radius){vector<Line> lines;for(int i=0;i<n;i++){Point a=p[i],b=p[(i+1)%n],offset=rotate90((b-a)/distance(a,b))*radius;lines.push_back(line(a+offset,b+offset));}return !halfplanes(lines).empty();};long double l=0,r=10000;for(int i=0;i<65;i++){long double mid=(l+r)/2;if(feasible(mid))l=mid;else r=mid;}cout << fixed << setprecision(12) << l << '\n';}''',
        '题目给的是凸多边形，到所有边内侧的距离约束才足够。输入以n=0结束。不能把质心当成最大内切圆圆心。',
        declarations=GEOMETRY+HPI,floating_output=True,complexity=r'时间 $O(n\log n\log(C/\varepsilon))$，空间 $O(n)$。')
    put(233770,2200,['半平面交','旋转卡壳','最大三角形'],'三个半径r圆完全在凸房间内，使三个圆心行列式绝对值最大。',
        '圆心可行域是房间各边向内平移r后的半平面交。输入顶点为顺时针，先反转成逆时针，再沿左法向量内缩。目标|w1+w2+w3|正是三个圆心构成三角形的二倍面积。固定另两点时面积对第三点是线性的，故最大值一定可在可行域顶点上取得。'
        '\n\n得到凸多边形后，枚举第一个顶点i，第二个顶点j沿序前进，用单调指针k找离ij最远的顶点；凸性保证k不回退。每个i花O(h)，总O(h²)。输出二倍面积即可，题目允许圆毯互相重叠。',
        r'''int tests;cin >> tests;while(tests--){int n;long double radius;cin >> n >> radius;vector<Point> p(n);for(auto &q:p)cin >> q.x >> q.y;reverse(p.begin(),p.end());vector<Line> lines;for(int i=0;i<n;i++){Point a=p[i],b=p[(i+1)%n],offset=rotate90((b-a)/distance(a,b))*radius;lines.push_back(line(a+offset,b+offset));}auto q=halfplanes(lines);int h=q.size();long double answer=0;for(int i=0;i<h;i++){int k=i+2;for(int j=i+1;j+1<h;j++){k=max(k,j+1);auto area=[&](int at){return cross(q[j]-q[i],q[at]-q[i]);};while(k+1<h && area(k+1)>area(k))k++;answer=max(answer,area(k));}}cout << fixed << setprecision(4) << answer << '\n';}''',
        '不需要给三个圆心互加距离≥2r的限制，题面并未禁止地毯重叠。行列式已经是题目价格，不能再除2。',
        declarations=GEOMETRY+HPI,floating_output=True,complexity=r'时间 $O(n\log n+h^2)$，空间 $O(n+h)$。')
    put(234015,2300,['凸多边形深度','半平面交','二分答案'],'选择总部位置，使敌人至少删除尽量多的凸包顶点才失去严格保护。',
        '删除任意k个塔后仍严格受保护，等价于总部在所有“跳过k个连续顶点”的弦的左侧。原因是：把总部划到凸包外的分割线，其外侧塔在凸包环上连续；若能用k个任意删除达到目的，也能只删这一段至多k个连续塔。'
        '\n\n将顶点改为逆时针。要让最少破坏数≥r，必须经得起删除r−1个塔，因此求所有有向弦P_i→P_(i+r)的左半平面交。总部必须严格在内部，交只有线段或一点时不合格，要有正面积。r增大时要求更强，二分最大可行r。上界floor((n−1)/2)：任一经过总部的直线两侧至少一侧不超过这个数量，边界本身也不受严格保护。',
        r'''int n;cin >> n;vector<Point> p(n);for(auto &q:p)cin >> q.x >> q.y;reverse(p.begin(),p.end());auto feasible=[&](int step){vector<Line> lines;for(int i=0;i<n;i++)lines.push_back(line(p[i],p[(i+step)%n]));auto q=halfplanes(lines);return q.size()>=3 && polygonArea(q)>1e-16L;};int l=1,r=(n+1)/2;while(r-l>1){int mid=(l+r)/2;if(feasible(mid))l=mid;else r=mid;}cout << l;''',
        '严格内部很关键：四个塔组成正方形时，两条对角线交点会在删去一个塔后的边界上，最优破坏数仍是1。只判断闭半平面交非空会算错。',
        declarations=GEOMETRY+HPI,complexity=r'时间 $O(n\log^2 n)$，空间 $O(n)$。')
    put(243845,2200,['CDQ分治','动态曼哈顿最近点','树状数组'],'在线序列只有插入点与查询最近曼哈顿距离，离线求每次答案。',
        r'先只考虑候选点$(x,y)$在询问$(X,Y)$左下方，即$x\le X,y\le Y$，距离是$X+Y-(x+y)$。按时间做CDQ，左半插入只能影响右半询问；左右按x归并扫描，用y上的树状数组维护左半插入的最大x+y，右半询问查y前缀即可。这样同时满足时间、x、y三维约束。'
        '\n\n分别将所有坐标乘上(+,+)、(+,-)、(-,+)、(-,-)四种符号，每次都求左下方候选，最后取四个方向距离最小。初始点作为早于所有操作的插入事件。CDQ递归返回时数组按x排序，但所属时间区间始终由归并前的划分固定。',
        r'''int n,m;cin >> n >> m;vector<Event> base;for(int i=0;i<n;i++){long long x,y;cin >> x >> y;base.push_back({x,y,1,-1,0});}int queries=0;for(int i=0;i<m;i++){int kind;long long x,y;cin >> kind >> x >> y;base.push_back({x,y,kind,kind==2?queries++:-1,0});}answer.assign(queries,LLONG_MAX);for(int sx:{-1,1})for(int sy:{-1,1}){event=base;vector<long long> coordinate;for(auto &q:event){q.x*=sx;q.y*=sy;coordinate.push_back(q.y);}sort(coordinate.begin(),coordinate.end());coordinate.erase(unique(coordinate.begin(),coordinate.end()),coordinate.end());for(auto &q:event)q.rank=lower_bound(coordinate.begin(),coordinate.end(),q.y)-coordinate.begin()+1;bit.assign(coordinate.size()+1,NEG);buffer.resize(event.size());cdq(0,event.size());}for(auto value:answer)cout << value << '\n';''',
        '树状数组维护最大值不能用减法回滚；每次归并完成后，将本轮更新经过的节点恢复负无穷。各递归层不同时保留树状数组状态，所以清空有效。',
        declarations=TIME_CDQ,complexity=r'时间 $O((n+m)\log^2(n+m))$，空间 $O(n+m)$。')
    put(236505,2200,['二维偏序','旋转坐标','离线扫描'],'相同角度区间光线照向其他星星，统计每个星星收到几次照射。',
        '角度从正x轴顺时针，且所有区间在[0,180)内。因此光源q一定在目标p的上方或同高。先计算Fθ(p)：向量p−q的顺时针角≤θ的光源数。0<θ<180时，这等价于q.y≥p.y，且sinθ*q.x+cosθ*q.y≤sinθ*p.x+cosθ*p.y。'
        '\n\n按y降序扫描，先加入同y的所有光源，再用旋转投影值上的树状数组查前缀。求区间[l,r]时用F≤r−F<l，严格版本把upper_bound改为lower_bound。同一点不照射自身，≤查询减去自身，严格<查询天然排除自身。θ=0单独按同一行从左向右计数。'
        '\n\n整数坐标能精确落在整数度数边界的非零向量，仅可能对应0、45、90、135度，分别用整数线性式处理，其他角使用long double。结果缓存相同端点的查询。',
        r'''int n,k;cin >> n >> k;vector<pair<int,int>> p(n);for(auto &q:p)cin >> q.first >> q.second;vector<pair<int,int>> interval(k);for(auto &q:interval)cin >> q.first >> q.second;map<pair<int,bool>,vector<int>> cache;auto calculate=[&](int degree,bool strict){vector<int> result(n);if(degree==0){if(strict)return result;vector<int> id(n);iota(id.begin(),id.end(),0);sort(id.begin(),id.end(),[&](int a,int b){return p[a].second!=p[b].second?p[a].second<p[b].second:p[a].first<p[b].first;});int start=0;for(int i=0;i<n;i++){if(i==0 || p[id[i]].second!=p[id[i-1]].second)start=i;result[id[i]]=i-start;}return result;}long double a=sinl(degree*acosl(-1.0L)/180),b=cosl(degree*acosl(-1.0L)/180);if(degree==45){a=1;b=1;}if(degree==90){a=1;b=0;}if(degree==135){a=1;b=-1;}vector<long double> value(n),coordinate;vector<int> order(n);for(int i=0;i<n;i++){value[i]=a*p[i].first+b*p[i].second;order[i]=i;}coordinate=value;sort(coordinate.begin(),coordinate.end());coordinate.erase(unique(coordinate.begin(),coordinate.end()),coordinate.end());sort(order.begin(),order.end(),[&](int x,int y){return p[x].second>p[y].second;});vector<int> bit(coordinate.size()+1);auto add=[&](int at){for(;at<(int)bit.size();at+=at&-at)bit[at]++;};for(int i=0;i<n;){int j=i;while(j<n && p[order[j]].second==p[order[i]].second){int id=order[j++];add(lower_bound(coordinate.begin(),coordinate.end(),value[id])-coordinate.begin()+1);}for(int at=i;at<j;at++){int id=order[at],rank=(strict?lower_bound(coordinate.begin(),coordinate.end(),value[id]):upper_bound(coordinate.begin(),coordinate.end(),value[id]))-coordinate.begin();int count=0;for(;rank;rank-=rank&-rank)count+=bit[rank];result[id]=count-!strict;}i=j;}return result;};vector<long long> answer(n);for(auto [l,r]:interval){for(auto [angle,strict,sign]:{tuple<int,bool,int>{r,false,1},{l,true,-1}}){auto key=make_pair(angle,strict);if(!cache.count(key))cache[key]=calculate(angle,strict);for(int i=0;i<n;i++)answer[i]+=sign*cache[key][i];}}for(auto x:answer)cout << x << ' ';''',
        '输入是顺时针角，不能沿用常见逆时针极角。边界包含，左端必须减严格小于l的数量。各光区互不相交，最终可直接求和。',
        complexity=r'时间 $O(kn\log n)$，缓存空间 $O(kn)$。')


if __name__=='__main__':run()
