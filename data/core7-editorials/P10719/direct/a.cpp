#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,k;cin>>n>>m>>k;vector<string>grid(n);for(auto &row:grid)cin>>row;int answer=n*m+1;
for(int top=0;top<n;++top){vector<int>columns(m);
    for(int bottom=top;bottom<n;++bottom){
        for(int c=0;c<m;++c)columns[c]+=grid[bottom][c]=='1';
        int left=0,black=0;
        for(int right=0;right<m;++right){black+=columns[right];
            while(left<=right&&black>=k){answer=min(answer,(bottom-top+1)*(right-left+1));black-=columns[left++];}
        }
    }
}
cout<<(answer==n*m+1?0:answer)<<'\n';
    return 0;
}
