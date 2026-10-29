#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
map<string,int> value;
string names[20]={"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen","twenty"};
for(int i=0;i<20;++i)value[names[i]]=i+1;
value["zero"]=0;
value["a"]=1;value["both"]=2;value["another"]=1;value["first"]=1;value["second"]=2;value["third"]=3;
vector<int> digits;for(int i=0;i<6;++i){string s;cin>>s;if(!s.empty()&&s.back()=='.')s.pop_back();for(char &c:s)c=tolower((unsigned char)c);if(value.count(s))digits.push_back(value[s]*value[s]%100);}
sort(digits.begin(),digits.end());string answer;
for(int x:digits){answer+=char('0'+x/10);answer+=char('0'+x%10);}
size_t p=answer.find_first_not_of('0');cout<<(p==string::npos?"0":answer.substr(p))<<'\n';
    return 0;
}
