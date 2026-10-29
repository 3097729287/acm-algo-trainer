#include <bits/stdc++.h>
using namespace std;
struct Student {string name; int x,y,z;};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<Student>a(n);for(auto &s:a)cin>>s.name>>s.x>>s.y>>s.z;
for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)
    if(abs(a[i].x-a[j].x)<=5&&abs(a[i].y-a[j].y)<=5&&abs(a[i].z-a[j].z)<=5
       &&abs(a[i].x+a[i].y+a[i].z-a[j].x-a[j].y-a[j].z)<=10)
        cout<<a[i].name<<' '<<a[j].name<<'\n';
    return 0;
}
