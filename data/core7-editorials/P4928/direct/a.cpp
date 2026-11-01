#include <bits/stdc++.h>
using namespace std;
struct Number{
    string digits="0";bool negative=false;
    Number()=default;
    Number(string text){
        size_t pos=0;
        if(!text.empty()&&(text[0]=='-'||text[0]=='+')){negative=text[0]=='-';++pos;}
        while(pos<text.size()&&text[pos]=='0') ++pos;
        digits=pos==text.size()?"0":text.substr(pos);
        if(digits=="0") negative=false;
    }
};
int absoluteCompare(const string &a,const string &b){
    if(a.size()!=b.size()) return a.size()<b.size()?-1:1;
    return a==b?0:(a<b?-1:1);
}
bool lessNumber(const Number &a,const Number &b){
    if(a.negative!=b.negative) return a.negative;
    int order=absoluteCompare(a.digits,b.digits);
    return a.negative?order>0:order<0;
}
string absoluteAdd(const string &a,const string &b){
    string result;int i=int(a.size())-1,j=int(b.size())-1,carry=0;
    while(i>=0||j>=0||carry){
        int value=carry;if(i>=0) value+=a[i--]-'0';if(j>=0) value+=b[j--]-'0';
        result.push_back(char('0'+value%10));carry=value/10;
    }
    reverse(result.begin(),result.end());return result;
}
// 前提：a 不小于 b；两个参数都只含绝对值数字。
string absoluteSubtract(const string &a,const string &b){
    string result;int j=int(b.size())-1,borrow=0;
    for(int i=int(a.size())-1;i>=0;--i){
        int value=a[i]-'0'-borrow-(j>=0?b[j--]-'0':0);borrow=value<0;
        if(borrow) value+=10;result.push_back(char('0'+value));
    }
    while(result.size()>1&&result.back()=='0') result.pop_back();
    reverse(result.begin(),result.end());return result;
}
Number plusNumber(const Number &a,const Number &b){
    Number result;
    if(a.negative==b.negative){result.digits=absoluteAdd(a.digits,b.digits);result.negative=a.negative;}
    else if(absoluteCompare(a.digits,b.digits)>=0){result.digits=absoluteSubtract(a.digits,b.digits);result.negative=a.negative;}
    else{result.digits=absoluteSubtract(b.digits,a.digits);result.negative=b.negative;}
    if(result.digits=="0") result.negative=false;return result;
}
Number timesSmall(const Number &a,int multiplier){
    Number result;if(!multiplier||a.digits=="0") return result;
    result.negative=a.negative^(multiplier<0);long long factor=multiplier;if(factor<0) factor=-factor;
    long long carry=0;string digits;
    for(int i=int(a.digits.size())-1;i>=0;--i){
        long long value=(a.digits[i]-'0')*factor+carry;digits.push_back(char('0'+value%10));carry=value/10;
    }
    while(carry){digits.push_back(char('0'+carry%10));carry/=10;}
    reverse(digits.begin(),digits.end());result.digits=digits;return result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<Number>color(n);for(auto &value:color){string text;cin>>text;value=Number(text);}
vector<int>wash(n),weather(m);for(int &x:wash) cin>>x;for(int &x:weather) cin>>x;
vector<int>power(n,1);int states=1;for(int i=0;i<n;++i){power[i]=states;states*=7;}
vector<vector<int>>transition(states,vector<int>(n,-1));
for(int state=0;state<states;++state){
    vector<int>age(n);int value=state,decayed=0;
    for(int i=0;i<n;++i){age[i]=value%7;value/=7;decayed+=max(0,age[i]-1)*power[i];}
    for(int i=0;i<n;++i) if(age[i]==0) transition[state][i]=decayed+wash[i]*power[i];
}
vector<Number>dp(states),next(states);vector<char>reachable(states),nextReachable(states);reachable[0]=true;
for(int day=0;day<m;++day){
    fill(nextReachable.begin(),nextReachable.end(),false);vector<Number>gain(n);
    for(int i=0;i<n;++i) gain[i]=timesSmall(color[i],weather[day]);
    bool any=false;
    for(int state=0;state<states;++state) if(reachable[state]) for(int i=0;i<n;++i){
        int target=transition[state][i];if(target<0) continue;
        Number candidate=plusNumber(dp[state],gain[i]);
        if(!nextReachable[target]||lessNumber(next[target],candidate)){next[target]=candidate;nextReachable[target]=true;any=true;}
    }
    if(!any){cout<<"gcd loves her clothes!\n";return 0;}
    dp.swap(next);reachable.swap(nextReachable);
}
Number answer;bool found=false;
for(int state=0;state<states;++state) if(reachable[state]&&(!found||lessNumber(answer,dp[state]))){answer=dp[state];found=true;}
if(answer.negative) cout<<'-';cout<<answer.digits<<'\n';
    return 0;
}
