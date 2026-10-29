#include <bits/stdc++.h>
using namespace std;
struct Scholar{int id,chinese,total;};
bool before(const Scholar&a,const Scholar&b){if(a.total!=b.total)return a.total>b.total;if(a.chinese!=b.chinese)return a.chinese>b.chinese;return a.id<b.id;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<Scholar>a(n);
for(int i=0;i<n;++i){int math,english;cin>>a[i].chinese>>math>>english;a[i].id=i+1;a[i].total=a[i].chinese+math+english;}
sort(a.begin(),a.end(),before);for(int i=0;i<5;++i)cout<<a[i].id<<' '<<a[i].total<<'\n';
    return 0;
}
