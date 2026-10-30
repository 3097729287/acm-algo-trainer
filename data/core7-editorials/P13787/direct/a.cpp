#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;int stride=n+2;vector<int>grid((size_t)stride*stride);
while(m--){int x1,y1,x2,y2;cin>>x1>>y1>>x2>>y2;
    ++grid[(size_t)x1*stride+y1];--grid[(size_t)(x2+1)*stride+y1];
    --grid[(size_t)x1*stride+y2+1];++grid[(size_t)(x2+1)*stride+y2+1];
}
long long answer=0;
for(int i=1;i<=n;++i)for(int j=1;j<=n;++j){size_t at=(size_t)i*stride+j;
    grid[at]+=grid[at-stride]+grid[at-1]-grid[at-stride-1];answer+=((i+j)^grid[at]);
}
cout<<answer<<'\n';
    return 0;
}
