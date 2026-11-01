#include <bits/stdc++.h>
using namespace std;
const long long MOD=998244353;
long long power(long long a,long long e){long long result=1;for(;e;e>>=1,a=a*a%MOD) if(e&1) result=result*a%MOD;return result;}
vector<long long> recurrence(const vector<long long>&s){
    vector<long long>C(1,1),B(1,1);int length=0,shift=1;long long last=1;
    for(int i=0;i<int(s.size());++i){
        long long error=s[i];for(int j=1;j<=length;++j) error=(error+C[j]*s[i-j])%MOD;
        if(error==0){++shift;continue;}
        auto old=C;long long factor=error*power(last,MOD-2)%MOD;
        if(C.size()<B.size()+shift) C.resize(B.size()+shift);
        for(int j=0;j<int(B.size());++j) C[j+shift]=(C[j+shift]-factor*B[j]%MOD+MOD)%MOD;
        if(2*length<=i){length=i+1-length;B=old;last=error;shift=1;}else ++shift;
    }
    C.resize(length+1);C.erase(C.begin());for(auto &x:C) x=(MOD-x)%MOD;return C;
}
long long term(const vector<long long>&s,const vector<long long>&rec,long long index){
    if(index<int(s.size())) return s[index];int d=rec.size();if(!d) return 0;
    auto multiply=[&](const vector<long long>&a,const vector<long long>&b){
        vector<long long>v(2*d-1);
        for(int i=0;i<d;++i) for(int j=0;j<d;++j) v[i+j]=(v[i+j]+a[i]*b[j])%MOD;
        for(int i=2*d-2;i>=d;--i) for(int j=1;j<=d;++j) v[i-j]=(v[i-j]+v[i]*rec[j-1])%MOD;
        v.resize(d);return v;
    };
    vector<long long>result(d),x(d);result[0]=1;if(d==1) x[0]=rec[0];else x[1]=1;
    for(;index;index>>=1,x=multiply(x,x)) if(index&1) result=multiply(result,x);
    long long answer=0;for(int i=0;i<d;++i) answer=(answer+result[i]*s[i])%MOD;return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string l;long long k;int m;cin>>l>>k>>m;int n=l.size(),ones=count(l.begin(),l.end(),'1');
vector<vector<long long>>choose(n+1,vector<long long>(n+1));choose[0][0]=1;
for(int i=1;i<=n;++i) for(int j=0;j<=i;++j) choose[i][j]=((j?choose[i-1][j-1]:0)+choose[i-1][j])%MOD;
vector<long long>less(n+1);int used=0;
for(int pos=0;pos<n;++pos) if(l[pos]=='1'){
    int remaining=n-pos-1;for(int j=0;j<=remaining;++j) less[used+j]=(less[used+j]+choose[remaining][j])%MOD;++used;
}
vector<long long>dp=less,sequence;long long tight=1;
for(int block=1;block<=2*(n+2);++block){
    long long sum=tight;for(long long x:dp) sum=(sum+x)%MOD;sequence.push_back(sum);
    vector<long long>prefix(n+1),next(n+1);prefix[0]=dp[0];for(int j=1;j<=n;++j) prefix[j]=(prefix[j-1]+dp[j])%MOD;
    for(int j=0;j<=n;++j){
        int limit=min(n,m-j);if(limit>=0) next[j]=choose[n][j]*prefix[limit]%MOD;
        if(j+ones<=m) next[j]=(next[j]+tight*less[j])%MOD;
    }
    tight=tight*(2*ones<=m);dp.swap(next);
}
cout<<term(sequence,recurrence(sequence),k-1)<<'\n';
    return 0;
}
