#include <bits/stdc++.h>
using namespace std;
struct Point{long long x,y;};vector<Point>points,buffer;
bool less_x(const Point&a,const Point&b){return a.x!=b.x?a.x<b.x:a.y<b.y;}
bool less_y(const Point&a,const Point&b){return a.y!=b.y?a.y<b.y:a.x<b.x;}
long long distance2(const Point&a,const Point&b){long long dx=a.x-b.x,dy=a.y-b.y;return dx*dx+dy*dy;}
long long closest(int l,int r){
    if(r-l<=3){
        long long best=LLONG_MAX;
        for(int i=l;i<r;++i)for(int j=i+1;j<r;++j)best=min(best,distance2(points[i],points[j]));
        sort(points.begin()+l,points.begin()+r,less_y);return best;
    }
    int mid=(l+r)/2;long long split_x=points[mid].x; // 子调用将改变排列，先保存中线
    long long best=min(closest(l,mid),closest(mid,r));
    int i=l,j=mid,k=l;
    while(i<mid&&j<r)buffer[k++]=less_y(points[i],points[j])?points[i++]:points[j++];
    while(i<mid)buffer[k++]=points[i++];while(j<r)buffer[k++]=points[j++];
    for(i=l;i<r;++i)points[i]=buffer[i];
    if(best==0)return 0;
    vector<Point>strip;
    for(i=l;i<r;++i){long long dx=points[i].x-split_x;if(dx*dx<best)strip.push_back(points[i]);}
    for(i=0;i<(int)strip.size();++i)for(j=i-1;j>=0;--j){
        long long dy=strip[i].y-strip[j].y;if(dy*dy>=best)break;
        best=min(best,distance2(strip[i],strip[j]));
    }
    return best;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;points.resize(n);buffer.resize(n);
for(auto &p:points)cin>>p.x>>p.y;
sort(points.begin(),points.end(),less_x);long long best=closest(0,n);
// 精确地将 sqrt(best) 四舍五入到万分之一
__int128 scaled=(__int128)best*100000000;long long lo=0,hi=20000000000000LL;
while(lo<hi){long long mid=lo+(hi-lo+1)/2;if((__int128)mid*mid<=scaled)lo=mid;else hi=mid-1;}
long long rounded=lo;__int128 odd=(__int128)2*lo+1;
if(4*scaled>=odd*odd)++rounded;
cout<<rounded/10000<<'.'<<setw(4)<<setfill('0')<<rounded%10000<<'\n';
    return 0;
}
