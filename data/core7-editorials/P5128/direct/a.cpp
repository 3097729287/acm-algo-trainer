#include <bits/stdc++.h>
using namespace std;
const int MOD=19260821;
void addmod(int &a,int b){a+=b;if(a>=MOD) a-=MOD;}
void submod(int &a,int b){a-=b;if(a<0) a+=MOD;}
struct History{int length=0,a=0,b=0,run=0;};
bool appendDigit(History &h,int d,int threshold){
    if(h.length==0){if(d){h.length=1;h.b=d;}return true;}
    if(h.length==1){h.length=2;h.a=h.b;h.b=d;h.run=2;return true;}
    h.run=(d-h.b==h.b-h.a)?h.run+1:2;h.a=h.b;h.b=d;
    return h.run<threshold;
}
int avoiding(const vector<int>&digits,int base,int threshold){
    int states=base*base*threshold;
    vector<int>pairCount(states),nextPair(states),one(base),nextOne(base);
    auto at=[&](int a,int b,int run){return (a*base+b)*threshold+run;};
    int empty=0;History tight;bool valid=true;
    for(int limit:digits){
        fill(nextPair.begin(),nextPair.end(),0);fill(nextOne.begin(),nextOne.end(),0);
        int nextEmpty=empty;
        for(int d=1;d<base;++d) nextOne[d]=empty;
        for(int b=0;b<base;++b){
            int total=one[b];
            for(int a=0;a<base;++a) for(int run=2;run<threshold;++run) addmod(total,pairCount[at(a,b,run)]);
            for(int c=0;c<base;++c) addmod(nextPair[at(b,c,2)],total);
        }
        for(int a=0;a<base;++a) for(int b=0;b<base;++b){
            int c=2*b-a;if(c<0||c>=base) continue;
            for(int run=2;run<threshold;++run){
                int count=pairCount[at(a,b,run)];submod(nextPair[at(b,c,2)],count);
                if(run+1<threshold) addmod(nextPair[at(b,c,run+1)],count);
            }
        }
        if(valid){
            for(int d=0;d<limit;++d){
                History h=tight;if(!appendDigit(h,d,threshold)) continue;
                if(h.length==0) addmod(nextEmpty,1);
                else if(h.length==1) addmod(nextOne[h.b],1);
                else addmod(nextPair[at(h.a,h.b,h.run)],1);
            }
            valid=appendDigit(tight,limit,threshold);
        }
        pairCount.swap(nextPair);one.swap(nextOne);empty=nextEmpty;
    }
    int answer=valid&&tight.length>0;
    for(int count:one) addmod(answer,count);
    for(int count:pairCount) addmod(answer,count);
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string decimal;int base;cin>>decimal>>base;int nmod=0;
for(char c:decimal) nmod=(nmod*10LL+c-'0')%MOD;
vector<int>digits;
while(decimal!="0"){
    string quotient;int remainder=0;
    for(char c:decimal){int value=remainder*10+c-'0';int q=value/base;remainder=value%base;if(q||!quotient.empty()) quotient+=char('0'+q);}
    digits.push_back(remainder);decimal=quotient.empty()?"0":quotient;
}
reverse(digits.begin(),digits.end());
int oneDigit=digits.size()==1?digits[0]:base-1;
int answer=(2LL*nmod-oneDigit+MOD)%MOD;
for(int threshold=3;threshold<=int(digits.size());++threshold){addmod(answer,nmod);submod(answer,avoiding(digits,base,threshold));}
cout<<answer<<'\n';
    return 0;
}
