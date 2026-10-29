#include <bits/stdc++.h>
using namespace std;
void print_row(const vector<int>&a){for(int i=0;i<(int)a.size();++i)cout<<a[i]<<(i+1==(int)a.size()?'\n':' ');}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;
    if(m==1){for(int i=0;i<n;++i)cout<<"1\n";continue;}
    if(n==1||(n%2==1&&m%2==0)){cout<<"-1\n";continue;}
    int start=0;
    if(n%2){int k=m/2;vector<int>p(m),q(m),r(m);
        for(int v=0;v<m;++v){int x=v,y=(v+k)%m,z=3*k-x-y;p[x]=q[y]=r[z]=v+1;}
        print_row(p);print_row(q);print_row(r);start=3;
    }
    for(int row=start;row<n;++row){for(int i=1;i<=m;++i)cout<<((row-start)%2==0?i:m+1-i)<<(i==m?'\n':' ');}
}
    return 0;
}
