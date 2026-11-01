#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long a,b;cin>>a>>b;
auto prefix=[&](long long x){
    if(x<=0) return 0LL;string digits=to_string(x);long long memo[20][11];memset(memo,-1,sizeof(memo));
    function<long long(int,int,bool)> dfs=[&](int pos,int previous,bool tight)->long long{
        if(pos==int(digits.size())) return previous!=10;
        if(!tight&&memo[pos][previous]>=0) return memo[pos][previous];
        long long count=0;int limit=tight?digits[pos]-'0':9;
        for(int d=0;d<=limit;++d){
            if(previous!=10&&abs(previous-d)<2) continue;
            int next=(previous==10&&d==0)?10:d;count+=dfs(pos+1,next,tight&&d==limit);
        }
        if(!tight) memo[pos][previous]=count;return count;
    };
    return dfs(0,10,true);
};
cout<<prefix(b)-prefix(a-1)<<'\n';
    return 0;
}
