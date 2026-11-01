#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long l,r;cin>>l>>r;
auto prefix=[&](long long x){
    if(x<10000000000LL) return 0LL;string digits=to_string(x);long long memo[12][11][4][2][4];memset(memo,-1,sizeof(memo));
    function<long long(int,int,int,bool,int,bool)> dfs=[&](int pos,int previous,int run,bool found,int seen,bool tight)->long long{
        if(pos==11) return found;long long &saved=memo[pos][previous][run][found][seen];if(!tight&&saved>=0) return saved;
        long long result=0;int limit=tight?digits[pos]-'0':9;
        for(int d=(pos==0?1:0);d<=limit;++d){
            int nextSeen=seen|(d==4?1:0)|(d==8?2:0);if(nextSeen==3) continue;
            int nextRun=d==previous?min(3,run+1):1;result+=dfs(pos+1,d,nextRun,found||nextRun==3,nextSeen,tight&&d==limit);
        }
        if(!tight) saved=result;return result;
    };
    return dfs(0,10,0,false,0,true);
};
cout<<prefix(r)-prefix(l-1)<<'\n';
    return 0;
}
