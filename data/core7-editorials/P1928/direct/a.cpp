#include <bits/stdc++.h>
using namespace std;
string encoded;size_t position=0;
string parse(){
    string result;
    while(position<encoded.size()&&encoded[position]!=']'){
        if(encoded[position]!='['){result.push_back(encoded[position++]);continue;}
        ++position;int times=0;
        while(position<encoded.size()&&'0'<=encoded[position]&&encoded[position]<='9')
            times=times*10+(encoded[position++]-'0');
        string part=parse();++position; // 内层停在 ]，本层消费该括号
        for(int k=0;k<times;++k)result+=part;
    }
    return result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>encoded;cout<<parse()<<'\n';
    return 0;
}
