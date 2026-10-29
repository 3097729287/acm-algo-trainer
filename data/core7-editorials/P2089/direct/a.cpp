#include <bits/stdc++.h>
using namespace std;
int target;vector<int>path;vector<vector<int>>answers;
void dfs(int pos,int sum){
    int remain=10-pos;if(sum+remain>target||sum+3*remain<target)return;
    if(pos==10){answers.push_back(path);return;}
    for(int x=1;x<=3;++x){path.push_back(x);dfs(pos+1,sum+x);path.pop_back();}
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>target;dfs(0,0);cout<<answers.size()<<'\n';
for(const auto &row:answers)for(int i=0;i<10;++i)cout<<row[i]<<(i==9?'\n':' ');
    return 0;
}
