#include <bits/stdc++.h>
using namespace std;
struct Number{
    string digits="0";bool negative=false;
    Number()=default;
    Number(string s){if(!s.empty()&&(s[0]=='-'||s[0]=='+')){negative=s[0]=='-';s.erase(s.begin());}
        size_t first=s.find_first_not_of('0');digits=first==string::npos?"0":s.substr(first);if(digits=="0")negative=false;}
};
int absolute_compare(const string &a,const string &b){if(a.size()!=b.size())return a.size()<b.size()?-1:1;return a==b?0:(a<b?-1:1);}
string absolute_add(const string &a,const string &b){string s;int i=int(a.size())-1,j=int(b.size())-1,carry=0;
    while(i>=0||j>=0||carry){int value=carry;if(i>=0)value+=a[i--]-'0';if(j>=0)value+=b[j--]-'0';s.push_back(char('0'+value%10));carry=value/10;}
    reverse(s.begin(),s.end());return s;}
// 前提：a 的绝对值不小于 b。
string absolute_subtract(const string &a,const string &b){string s;int j=int(b.size())-1,borrow=0;
    for(int i=int(a.size())-1;i>=0;--i){int value=a[i]-'0'-borrow-(j>=0?b[j--]-'0':0);borrow=value<0;if(borrow)value+=10;s.push_back(char('0'+value));}
    while(s.size()>1&&s.back()=='0')s.pop_back();reverse(s.begin(),s.end());return s;}
Number plus_number(Number a,Number b){Number result;if(a.negative==b.negative){result.digits=absolute_add(a.digits,b.digits);result.negative=a.negative;}
    else{if(absolute_compare(a.digits,b.digits)<0)swap(a,b);result.digits=absolute_subtract(a.digits,b.digits);result.negative=a.negative;}
    if(result.digits=="0")result.negative=false;return result;}
Number times_small(Number a,long long multiplier){Number result;if(!multiplier||a.digits=="0")return result;
    result.negative=a.negative^(multiplier<0);if(multiplier<0)multiplier=-multiplier;long long carry=0;string s;
    for(int i=int(a.digits.size())-1;i>=0;--i){long long value=(a.digits[i]-'0')*multiplier+carry;s.push_back(char('0'+value%10));carry=value/10;}
    while(carry){s.push_back(char('0'+carry%10));carry/=10;}reverse(s.begin(),s.end());result.digits=s;return result;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<Number>state(n+1),threshold(n+1);for(int u=1;u<=n;++u){string c,t;cin>>c>>t;state[u]=Number(c);threshold[u]=Number(t);}
vector<vector<pair<int,long long>>>graph(n+1);vector<int>indegree(n+1);
for(int i=0;i<m;++i){int u,v;long long w;cin>>u>>v>>w;graph[u].push_back({v,w});++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);else{threshold[u].negative=!threshold[u].negative;state[u]=plus_number(state[u],threshold[u]);}
while(!ready.empty()){int u=ready.front();ready.pop();for(auto [v,w]:graph[u]){
    if(!state[u].negative&&state[u].digits!="0")state[v]=plus_number(state[v],times_small(state[u],w));
    if(--indegree[v]==0)ready.push(v);
}}
bool any=false;for(int u=1;u<=n;++u)if(graph[u].empty()&&!state[u].negative&&state[u].digits!="0"){cout<<u<<' '<<state[u].digits<<'\n';any=true;}if(!any)cout<<"NULL\n";
    return 0;
}
