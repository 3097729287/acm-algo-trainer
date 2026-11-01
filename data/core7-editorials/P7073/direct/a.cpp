#include <bits/stdc++.h>
using namespace std;
struct Node{char kind;int left,right,variable;};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string expression;getline(cin,expression);vector<Node>nodes;vector<int>stack,leaf(1);
for(size_t at=0;at<expression.size();){
    if(expression[at]==' '){++at;continue;}
    if(expression[at]=='x'){++at;int variable=0;while(at<expression.size()&&expression[at]>='0'&&expression[at]<='9')variable=variable*10+expression[at++]-'0';
        if((int)leaf.size()<=variable)leaf.resize(variable+1);leaf[variable]=(int)nodes.size();nodes.push_back({'v',-1,-1,variable});stack.push_back((int)nodes.size()-1);
    }else{char kind=expression[at++];int right=stack.back();stack.pop_back();int left=right;
        if(kind!='!'){left=stack.back();stack.pop_back();}nodes.push_back({kind,left,right,0});stack.push_back((int)nodes.size()-1);
    }
}
int n;cin>>n;vector<int>initial(n+1);for(int i=1;i<=n;++i)cin>>initial[i];
vector<int>value(nodes.size()),important(nodes.size());
for(size_t i=0;i<nodes.size();++i){auto u=nodes[i];if(u.kind=='v')value[i]=initial[u.variable];else if(u.kind=='!')value[i]=value[u.left]^1;else if(u.kind=='&')value[i]=value[u.left]&value[u.right];else value[i]=value[u.left]|value[u.right];}
int root=stack.back();important[root]=1;
for(int i=(int)nodes.size()-1;i>=0;--i)if(important[i]){auto u=nodes[i];if(u.kind=='!')important[u.left]=1;
    else if(u.kind=='&'){if(value[u.right])important[u.left]=1;if(value[u.left])important[u.right]=1;}
    else if(u.kind=='|'){if(!value[u.right])important[u.left]=1;if(!value[u.left])important[u.right]=1;}
}
int queries;cin>>queries;while(queries--){int variable;cin>>variable;cout<<(value[root]^important[leaf[variable]])<<'\n';}
    return 0;
}
