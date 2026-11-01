#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>height(m);long long answer=0;
for(int row=0;row<n;++row){string line;cin>>line;vector<pair<int,int>>stack;long long suffixSum=0;
    for(int j=0;j<m;++j){height[j]=line[j]=='.'?height[j]+1:0;int width=1;while(!stack.empty()&&stack.back().first>=height[j]){suffixSum-=1LL*stack.back().first*stack.back().second;width+=stack.back().second;stack.pop_back();}stack.push_back({height[j],width});suffixSum+=1LL*height[j]*width;answer+=suffixSum;}
}
cout<<answer<<'\n';
    return 0;
}
