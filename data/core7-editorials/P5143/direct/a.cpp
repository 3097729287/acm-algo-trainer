#include <bits/stdc++.h>
using namespace std;
struct Point{long double x,y,z;};
bool lower_point(const Point&a,const Point&b){return a.z<b.z;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<Point>a(n);for(auto &p:a)cin>>p.x>>p.y>>p.z;sort(a.begin(),a.end(),lower_point);
long double answer=0;for(int i=1;i<n;++i)answer+=hypot(a[i].x-a[i-1].x,a[i].y-a[i-1].y,a[i].z-a[i-1].z);
cout<<fixed<<setprecision(3)<<answer<<'\n';
    return 0;
}
