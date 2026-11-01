#include <bits/stdc++.h>
using namespace std;
long long allAtLeast(const vector<vector<int>>&g,int threshold){
    int n=g.size();vector<int>height(n);long long answer=0;
    for(int row=0;row<n;++row){vector<pair<int,int>>stack;long long sum=0;
        for(int j=0;j<n;++j){height[j]=g[row][j]>=threshold?height[j]+1:0;int width=1;while(!stack.empty()&&stack.back().first>=height[j]){sum-=1LL*stack.back().first*stack.back().second;width+=stack.back().second;stack.pop_back();}stack.push_back({height[j],width});sum+=1LL*height[j]*width;answer+=sum;}
    }
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>g(n,vector<int>(n));for(auto &row:g) for(int &x:row) cin>>x;cout<<allAtLeast(g,100)-allAtLeast(g,101)<<'\n';
    return 0;
}
