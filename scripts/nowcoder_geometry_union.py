"""Exact strip arrangement sides and incremental collinear-circle union."""
from nowcoder_editorials import CONTENT,add,read

SPARK=r'''
using Wide=__int128_t;
struct Fraction{
    long long a,b;
    Fraction(long long x=0,long long y=1):a(x),b(y){if(b<0){a=-a;b=-b;}}
    bool operator<(const Fraction &v)const{return (Wide)a*v.b<(Wide)v.a*b;}
    bool operator==(const Fraction &v)const{return (Wide)a*v.b==(Wide)v.a*b;}
};
struct Strip{long long a,b,c,d;};
struct Boundary{long long a,b,c,sign;};
bool uncovered(const Boundary &line,const vector<Strip> &strips,long long X,long long Y){
    auto [a,b,c,sign]=line;
    Fraction low,high;
    if(b){
        low=Fraction(0);high=Fraction(X);
        if(a){Fraction x(c,a),y(c-b*Y,a);if(y<x)swap(x,y);low=max(low,x);high=min(high,y);}
        else{Fraction y(c,b);if(y<Fraction(0) || Fraction(Y)<y)return false;}
    }else{
        Fraction x(c,a);if(x<Fraction(0) || Fraction(X)<x)return false;low=Fraction(0);high=Fraction(Y);
    }
    if(!(low<high))return false;
    if(!b){Fraction x(c,a);if((x==Fraction(0) && sign*a<0) || (x==Fraction(X) && sign*a>0))return false;}
    if(!a){Fraction y(c,b);if((y==Fraction(0) && sign*b<0) || (y==Fraction(Y) && sign*b>0))return false;}
    vector<pair<Fraction,Fraction>> interval;
    long long norm=a*a+b*b;
    for(auto s:strips){
        long long parallel=a*s.b-b*s.a;
        if(!parallel){
            long long value=c*(a*s.a+b*s.b),lower=s.c*norm,upper=s.d*norm,move=sign*(a*s.a+b*s.b);
            if(lower<value && value<upper)return false;
            if(s.c!=s.d && ((value==lower && move>0) || (value==upper && move<0)))return false;
            continue;
        }
        Fraction l,r;
        if(b){long long coefficient=s.a*b-s.b*a;l=Fraction(s.c*b-s.b*c,coefficient);r=Fraction(s.d*b-s.b*c,coefficient);}
        else{l=Fraction(s.c*a-s.a*c,s.b*a);r=Fraction(s.d*a-s.a*c,s.b*a);}
        if(r<l)swap(l,r);l=max(l,low);r=min(r,high);if(l<r)interval.push_back({l,r});
    }
    sort(interval.begin(),interval.end(),[](const auto &x,const auto &y){return x.first<y.first;});
    Fraction reach=low;
    for(auto [l,r]:interval){if(reach<l)return true;reach=max(reach,r);}
    return reach<high;
}
'''
PLATES=r'''
using Wide=__int128_t;
struct Disc{long long x,r;long long intercept()const{return r*r-x*x;}};
map<long long,Disc> hull;
long double total=0,compensation=0;
void accumulate(long double value){long double adjusted=value-compensation,next=total+adjusted;compensation=(next-total)-adjusted;total=next;}
long double contribution(map<long long,Disc>::iterator it){
    if(it==hull.end())return 0;
    Disc d=it->second;long double l=d.x-d.r,r=d.x+d.r;
    auto crossing=[](const auto &a,const auto &b){return (long double)(a.second.intercept()-b.second.intercept())/(b.first-a.first);};
    if(it!=hull.begin())l=max(l,crossing(*prev(it),*it));
    if(next(it)!=hull.end())r=min(r,crossing(*it,*next(it)));
    if(l>=r)return 0;
    auto primitive=[&](long double x){long double t=clamp(x-d.x,-(long double)d.r,(long double)d.r),radius=d.r;return t*sqrtl(max(0.0L,radius*radius-t*t))+radius*radius*asinl(clamp(t/radius,-1.0L,1.0L));};
    return primitive(r)-primitive(l);
}
void eraseLine(map<long long,Disc>::iterator it){
    auto left=it==hull.begin()?hull.end():prev(it),right=next(it);
    accumulate(-contribution(left));accumulate(-contribution(it));accumulate(-contribution(right));
    hull.erase(it);accumulate(contribution(left));accumulate(contribution(right));
}
bool redundant(map<long long,Disc>::iterator it){
    if(it==hull.begin() || next(it)==hull.end())return false;
    auto a=prev(it),b=it,c=next(it);
    return (Wide)(a->second.intercept()-b->second.intercept())*(c->first-b->first)>=(Wide)(b->second.intercept()-c->second.intercept())*(b->first-a->first);
}
void insertDisc(Disc d){
    long long slope=2*d.x;auto old=hull.find(slope);
    if(old!=hull.end()){if(old->second.r>=d.r)return;eraseLine(old);}
    auto right=hull.lower_bound(slope),left=right==hull.begin()?hull.end():prev(right);
    accumulate(-contribution(left));accumulate(-contribution(right));
    auto it=hull.emplace(slope,d).first;
    accumulate(contribution(left));accumulate(contribution(it));accumulate(contribution(right));
    if(redundant(it)){eraseLine(it);return;}
    while(it!=hull.begin() && redundant(prev(it)))eraseLine(prev(it));
    while(next(it)!=hull.end() && redundant(next(it)))eraseLine(next(it));
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(238005,2300,['直线排列','有理数比较','区间并'],'在矩形0≤x≤X、0≤y≤Y内，判断是否存在不落入任何闭条带C≤Ax+By≤D的点。',
        '本地原题正文漏掉了区域的数学定义，上述题意依据[原比赛题面](https://codeforces.com/gym/103447/problem/F)补全。条带包含边界，目标是严格避开全部条带。'
        '\n\n若存在安全点，安全区域作为有限个闭条带的补集，具有一小块二维开区域。该区域边界必有一段来自矩形边或某条带边界的线段。于是枚举4条矩形边（向内侧移动）和每个条带两条边（向条带外侧移动），寻找某段边界，沿指定侧无限小移动后仍安全。'
        '\n\n固定候选直线Ax+By=C，用x作参数（竖直线改用y），先截取矩形内的参数区间。其他非平行条带在线上覆盖一个闭区间，把这些区间求并；有正长度空隙，就可从空隙中点向指定侧移动。平行条带单独处理：若整条线在其内部，或恰在边界且指定移动方向进入该条带，候选整条作废；零宽条带不阻止向任一侧离开。若候选线在矩形边上，还要保证指定方向进入矩形。'
        '\n\n交点参数全部保存为整数分子、正分母，用128位交叉相乘比较，因此即使安全区域很窄，也不会因浮点面积消失。仅有单点空隙不算安全段，区间端点相接时没有间隙。',
        r'''int tests;cin >> tests;string answer;while(tests--){long long X,Y;int n;cin >> X >> Y >> n;vector<Strip> strips(n);vector<Boundary> boundary={{1,0,0,1},{1,0,X,-1},{0,1,0,1},{0,1,Y,-1}};for(auto &s:strips){cin >> s.a >> s.b >> s.c >> s.d;boundary.push_back({s.a,s.b,s.c,-1});boundary.push_back({s.a,s.b,s.d,1});}bool found=false;for(auto l:boundary)if(uncovered(l,strips,X,Y)){found=true;break;}answer.push_back(found?'1':'0');}cout << answer;''',
        '“只看矩形四个角”会漏掉内部安全洞。只对条带并面积做浮点比较，也可能把极窄安全区误判为全覆盖。参数区间与平行侧别均需精确处理。',
        declarations=SPARK,complexity=r'每组时间 $O(n^2\log n)$，空间 $O(n)$；各组n总和≤2000。')
    put(230850,2300,['动态凸壳','圆面积并','分段积分'],'圆心全部在x轴，每插入一个圆盘立即求总覆盖面积。',
        r'上半圆高度平方是$r_i^2-(x-x_i)^2=-x^2+(2x_i x+r_i^2-x_i^2)$。公共项−x²不影响最大值，所以圆盘并的上边界，由直线$L_i(x)=2x_i x+r_i^2-x_i^2$的上包络决定。再将负的高度平方截为0，下半平面对称。'
        '\n\n用按斜率有序的map维护上凸壳。相同圆心只保留最大半径；若连续三条线的相邻交点不递增，中间线永远不胜出，应删除。插入后只可能删掉两侧相邻的一段线，每条线至多被删一次。交点次序用128位整数比较。'
        '\n\n每条保留线在与左右邻线的交点之间获胜，再与该圆自己的[x_i−r_i,x_i+r_i]相交。这个区间的面积贡献为2倍上半圆积分，其原函数为t*sqrt(r²−t²)+r²*asin(t/r)，t=x−x_i。插入、删除一条线，只会改动它和左右邻线的贡献：先减旧贡献，变更map，再加新贡献。用long double和补偿求和控制大量面积增减的误差。',
        r'''int n;cin >> n;while(n--){Disc d;cin >> d.x >> d.r;insertDisc(d);cout << fixed << setprecision(12) << max(0.0L,total) << '\n';}''',
        '圆盘不能只按相邻圆心的两圆交面积容斥，会漏掉多圆重叠及包含。包络线即使在某段高度平方为负，也应保留到几何积分时再截零。',
        declarations=PLATES,floating_output=True,complexity=r'总时间 $O(n\log n)$，空间 $O(n)$；每条线只插入、删除一次。')


if __name__=='__main__':run()
