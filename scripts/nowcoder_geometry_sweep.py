"""Intersection decision sweeps and an exact angular wall-count sweep."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_geometry_support import GEOMETRY,INTEGER

CAR_SWEEP=r'''
struct Car{Point p,d,v;long double speed;long long x,y,dx,dy;};
vector<Car> car;
vector<pair<Point,Point>> segment;
long double sweepX,duration;
long double height(int i){auto [a,b]=segment[i];if(a.x>b.x)swap(a,b);long double x=clamp(sweepX,a.x,b.x);return a.y+(b.y-a.y)*(x-a.x)/(b.x-a.x);}
struct Order{bool operator()(int a,int b)const{long double x=height(a),y=height(b);return x!=y?x<y:a<b;}};
long double collision(int i,int j){
    const auto &a=car[i];const auto &b=car[j];
    long long x=b.x-a.x,y=b.y-a.y,den=a.dx*b.dy-a.dy*b.dx;
    if(den){long double u=(long double)(x*b.dy-y*b.dx)/den,v=(long double)(x*a.dy-y*a.dx)/den;if(u<0 || v<0)return 1e100L;return max(u*norm(a.d)/a.speed,v*norm(b.d)/b.speed);}
    if(x*a.dy-y*a.dx)return 1e100L;
    long double z=dot(b.p-a.p,a.d)/norm(a.d);
    if(dot(a.d,b.d)>0)return z>=0?z/a.speed:-z/b.speed;
    return z>=0?z/(a.speed+b.speed):1e100L;
}
bool canCrash(long double time){
    duration=time;int n=car.size();segment.resize(n);
    struct Event{long double x;int kind,id;};vector<Event> event;
    for(int i=0;i<n;i++){Point a=car[i].p,b=a+car[i].v*time;if(a.x>b.x)swap(a,b);segment[i]={a,b};event.push_back({a.x,0,i});event.push_back({b.x,1,i});}
    sort(event.begin(),event.end(),[](auto a,auto b){return a.x!=b.x?a.x<b.x:a.kind<b.kind;});
    set<int,Order> active;vector<set<int,Order>::iterator> position(n);
    auto intersect=[&](int a,int b){return collision(a,b)<=time;};
    for(auto e:event){sweepX=e.x;if(e.kind==0){auto it=active.insert(e.id).first;position[e.id]=it;if(it!=active.begin() && intersect(*prev(it),*it))return true;if(next(it)!=active.end() && intersect(*it,*next(it)))return true;}
        else{auto it=position[e.id],right=next(it);if(it!=active.begin() && right!=active.end() && intersect(*prev(it),*right))return true;active.erase(it);}}
    return false;
}
'''
CAPSULE_SWEEP=r'''
struct Segment{Point a,b;};
vector<Segment> segment;
long double sweepX,threshold;
long double height(int i){auto [a,b]=segment[i];if(a.x==b.x)return (a.y+b.y)/2;long double x=clamp(sweepX,a.x,b.x);return a.y+(b.y-a.y)*(x-a.x)/(b.x-a.x);}
struct Order{bool operator()(int a,int b)const{long double x=height(a),y=height(b);return x!=y?x<y:a<b;}};
long double pointDistance(Point p,const Segment &s){Point e=s.b-s.a;long double t=clamp(dot(p-s.a,e)/dot(e,e),0.0L,1.0L);return distance(p,s.a+e*t);}
long double segmentDistance(int i,int j){auto a=segment[i],b=segment[j];return min({pointDistance(a.a,b),pointDistance(a.b,b),pointDistance(b.a,a),pointDistance(b.b,a)});}
bool within(long double gap,const vector<int> &start,const vector<int> &finish){
    int n=segment.size();long double radius=gap/2;set<int,Order> active;vector<set<int,Order>::iterator> position(n);
    auto close=[&](int a,int b){return segmentDistance(a,b)<=gap;};
    int i=0,j=0;
    while(i<n || j<n){bool enter=j==n || (i<n && segment[start[i]].a.x-radius<=segment[finish[j]].b.x+radius);
        int id=enter?start[i++]:finish[j++];sweepX=enter?segment[id].a.x-radius:segment[id].b.x+radius;
        if(enter){auto it=active.insert(id).first;position[id]=it;if(it!=active.begin() && close(*prev(it),*it))return true;if(next(it)!=active.end() && close(*it,*next(it)))return true;}
        else{auto it=position[id],right=next(it);if(it!=active.begin() && right!=active.end() && close(*prev(it),*right))return true;active.erase(it);}}
    return false;
}
'''
WALLS=r'''
#include <ext/pb_ds/assoc_container.hpp>
#include <ext/pb_ds/tree_policy.hpp>
using namespace __gnu_pbds;
struct Wall{IPoint a,b;};
vector<Wall> wall;
IPoint origin,direction;
pair<Wide,Wide> rayTime(int id){
    if(id<0)return {1,1};
    IPoint edge=wall[id].b-wall[id].a;Wide a=cross(wall[id].a-origin,edge),b=cross(direction,edge);
    if(b<0){a=-a;b=-b;}return {a,b};
}
struct RayOrder{
    bool operator()(int a,int b)const{
        auto x=rayTime(a),y=rayTime(b);Wide left=x.first*y.second,right=y.first*x.second;
        return left!=right?left<right:a<b;
    }
};
using Active=tree<int,null_type,RayOrder,rb_tree_tag,tree_order_statistics_node_update>;
vector<int> crossings(const vector<IPoint> &point,int source){
    origin=point[source];direction={1,0};
    struct Event{IPoint d;int kind,id;};vector<Event> event;vector<int> initial;
    for(int i=0;i<(int)wall.size();i++){
        IPoint a=wall[i].a-origin,b=wall[i].b-origin;
        if((a.x==0 && a.y==0)||(b.x==0 && b.y==0))continue;
        Wide c=cross(a,b);if(!c)continue;if(c<0)swap(a,b);
        event.push_back({a,2,i});event.push_back({b,0,i});if(angleLess(b,a))initial.push_back(i);
    }
    for(int i=0;i<(int)point.size();i++)if(i!=source){IPoint d=point[i]-origin;if(d.x || d.y)event.push_back({d,1,i});}
    sort(event.begin(),event.end(),[](const Event &a,const Event &b){if(angleLess(a.d,b.d))return true;if(angleLess(b.d,a.d))return false;return a.kind!=b.kind?a.kind<b.kind:a.id<b.id;});
    Active active;for(int id:initial)active.insert(id);
    vector<int> result(point.size());
    for(auto e:event){direction=e.d;if(e.kind==0)active.erase(e.id);else if(e.kind==2)active.insert(e.id);else result[e.id]=active.order_of_key(-1);}
    return result;
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(238004,2300,['二分答案','线段相交扫描线','射线交点'],'各车可延迟启动但只沿固定射线前进，求最早能安排碰撞的时间。',
        '给定结束时间T，第i辆车能到达射线上从起点到p_i+v_i*T的整条线段；能安排碰撞当且仅当某两条这样的线段相交。若车提前到达交点，可把启动时刻延后，让两车同时到达。可行性对T单调，用二分。'
        '\n\n相交判定用竖直扫描线：按线段左右端点排序，维护当前线段的上下顺序，插入时检查新出现的两对邻居，删除时检查被连成新邻居的一对。若真有相交，在首次相交前线段次序不会改变，相交双方一定会先成为邻居，因此不会漏判。比较器随扫描x变化，仅在尚未发现交点的前提下维护有序结构；检查的是整条线段是否相交，发现后立即结束。'
        '\n\n两车检查直接由原始整数射线计算最早碰撞时间，避免用巨大T生成的端点做不稳定叉积。非平行时求唯一射线交点，并取两车到达时间最大值；同向共线时后车追到前车起点，反向相向时双方同时开动，背向则无解。上界10^13超过本题整数坐标、方向参数能产生的有限交会时间。'
        '\n\n扫描线思路可对照[原比赛讲解](https://codeforces.com/blog/entry/78116)。下面代码独立实现射线到达时间与端点事件。',
        r'''int n;cin >> n;car.resize(n);for(auto &a:car){cin >> a.x >> a.y >> a.dx >> a.dy >> a.speed;a.p={(long double)a.x,(long double)a.y};a.d={(long double)a.dx,(long double)a.dy};a.v=a.d*(a.speed/norm(a.d));}long double l=0,r=1e13L;if(!canCrash(r)){cout << "No show :(";return 0;}for(int i=0;i<75;i++){long double mid=(l+r)/2;if(canCrash(mid))r=mid;else l=mid;}cout << fixed << setprecision(15) << r;''',
        '速度si是长度/秒，应将方向向量归一化。不能要求两车从0时刻同时启动。起点互异，但共线射线仍需专门处理。',
        declarations=GEOMETRY+CAR_SWEEP,floating_output=True,complexity=r'时间 $O(n\log n\log(C/\varepsilon))$，空间 $O(n)$。')
    put(230839,2300,['胶囊形','二分答案','扫描线'],'互不相交的n条线段之间，求最近距离。',
        '两条线段最近点至少有一个是端点，因此两线段距离是四个“端点到另一线段距离”的最小值。为避免枚举全部线段对，二分距离d，把每条线段膨胀半径d/2，得到线段加圆盘的胶囊形；存在两胶囊相交，当且仅当原线段最近距离≤d。'
        '\n\n每个胶囊是凸集，竖直截面是区间。按最左x−d/2插入、最右x+d/2删除，用有序集合维护竖直次序，每次只检查新增邻居的两胶囊是否相交。尚未相交时相对上下次序稳定；首次接触前必成为邻居。比较时可取原线段在扫描x处的y，x超出原线段范围时夹到最近端点；这个点总在胶囊截面内，足以确定两个不相交胶囊的次序，竖直线段取中点y。'
        '\n\n插入序列与删除序列分别只需按原线段最左、最右x排序一次，每轮二分线性归并这两个事件序列。原线段互不相交是题目保证，所以距离计算无需再做线段相交分支。',
        r'''int tests;cin >> tests;while(tests--){int n;cin >> n;segment.resize(n);vector<int> start(n),finish(n);for(int i=0;i<n;i++){auto &s=segment[i];cin >> s.a.x >> s.a.y >> s.b.x >> s.b.y;if(s.a.x>s.b.x)swap(s.a,s.b);start[i]=finish[i]=i;}sort(start.begin(),start.end(),[](int a,int b){return segment[a].a.x<segment[b].a.x;});sort(finish.begin(),finish.end(),[](int a,int b){return segment[a].b.x<segment[b].b.x;});long double l=0,r=segmentDistance(0,1);for(int i=1;i<min(n,100);i++)r=min(r,segmentDistance(i-1,i));for(int i=0;i<55;i++){long double mid=(l+r)/2;if(within(mid,start,finish))r=mid;else l=mid;}cout << fixed << setprecision(15) << r << '\n';}''',
        '只比较原始端点的最近点对会漏掉“端点到长线段内部”的距离。胶囊的排序代表点必须落在当前竖直截面内，不能无限外推原直线。',
        declarations=GEOMETRY+CAPSULE_SWEEP,floating_output=True,complexity=r'时间 $O(n\log n\log(C/\varepsilon))$，空间 $O(n)$。')
    put(232803,2300,['角度扫描线','最短路','严格相交'],'穿过每道互不相交的轴平行冰墙加k时间，求s到t的欧氏距离加穿墙代价最小值。',
        '最短路径的转折只需发生在冰墙端点：在其他位置弯折，可以局部拉直且不改变严格穿墙次数。建立s、t和全部墙端点为节点的完全图，直连边权=欧氏距离+k*严格穿过的墙数，再跑Dijkstra。关键是将逐边数墙的O(n³)降下来。'
        '\n\n从一个源点出发，将射线绕一周扫描。每道不经过源点的墙占据一个小于π的开角区间，进入时加入、离开时删除。墙两两不相交，因此当前射线与各墙交点由近到远的顺序不会变化。用支持排名的平衡树维护交点距离；射线对准一个目标时，查询交点参数t<1的墙数。'
        '\n\n端点角度相同时，先删除结束的墙，再查询目标，最后加入开始的墙，所以射线仅碰墙端点不算穿墙；与源点相接的墙也不计。交点参数用整数叉积组成的分数，比较时用128位相乘。每个Dijkstra选中的节点执行一次角度扫描，随即松弛其他节点，无需存整张完全图。代码使用GNU C++17的PBDS排名树。',
        r'''int tests;cin >> tests;while(tests--){int n;long long penalty;cin >> n >> penalty;wall.resize(n);vector<IPoint> point;for(auto &s:wall){cin >> s.a.x >> s.a.y >> s.b.x >> s.b.y;point.push_back(s.a);point.push_back(s.b);}IPoint s,t;cin >> s.x >> s.y >> t.x >> t.y;point.push_back(s);point.push_back(t);int count=point.size(),source=count-2,target=count-1;vector<long double> dist(count,1e100L);vector<bool> used(count);dist[source]=0;for(int step=0;step<count;step++){int v=-1;for(int i=0;i<count;i++)if(!used[i] && (v<0 || dist[i]<dist[v]))v=i;if(v==target)break;used[v]=true;auto crossed=crossings(point,v);for(int u=0;u<count;u++)if(!used[u]){IPoint d=point[u]-point[v];long double value=dist[v]+sqrtl((long double)dot(d,d))+(long double)penalty*crossed[u];dist[u]=min(dist[u],value);}}cout << fixed << setprecision(12) << dist[target] << '\n';}''',
        '经过端点和沿墙移动均不收穿墙代价。把角区间设为闭区间会使经过端点的最短路多收k。不可用不支持排名的普通set再线性数前驱。',
        declarations=INTEGER+WALLS,floating_output=True,complexity=r'节点数V=2n+2，总时间 $O(Vn\log n+V^2)$，空间 $O(V+n)$。')


if __name__=='__main__':run()
