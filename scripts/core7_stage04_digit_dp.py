"""Exact programs for the digit, ranking and positional-counting unit."""
CODE={}
DECL={}

CODE['P2657']=r'''
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
'''

CODE['P14074']=r'''
long long l,r;cin>>l>>r;
auto prefix=[&](long long x){
    if(x<0) return 0LL;long long count[2][2]={},sum[2][2]={};count[1][0]=1;
    for(int pos=30;pos>=0;--pos){
        long long nextCount[2][2]={},nextSum[2][2]={};int bit=(x>>pos)&1;
        for(int tight=0;tight<2;++tight) for(int parity=0;parity<2;++parity){
            int limit=tight?bit:1;
            for(int d=0;d<=limit;++d){
                int nt=tight&&d==limit,np=parity^d;
                nextCount[nt][np]+=count[tight][parity];nextSum[nt][np]+=2*sum[tight][parity]+d*count[tight][parity];
            }
        }
        for(int t=0;t<2;++t) for(int p=0;p<2;++p){count[t][p]=nextCount[t][p];sum[t][p]=nextSum[t][p];}
    }
    return sum[0][1]+sum[1][1];
};
cout<<prefix(r)-prefix(l-1)<<'\n';
'''

DECL['P1836']=r'''
long long prefix(long long n){
    if(n<=0) return 0;long long answer=0;
    for(long long place=1;;place*=10){
        long long high=n/place/10,current=n/place%10,low=n%place;
        answer+=high*45*place+current*(current-1)/2*place+current*(low+1);
        if(place>n/10) break;
    }
    return answer;
}
'''
CODE['P1836']=r'''long long n;cin>>n;cout<<prefix(n)<<'\n';'''
DECL['SP17247']=DECL['P1836']
CODE['SP17247']=r'''int t;cin>>t;while(t--){long long a,b;cin>>a>>b;cout<<prefix(b)-prefix(a-1)<<'\n';}'''

DECL['P4999']=r'''
const long long MOD=1000000007;
long long prefix(long long n){
    if(n<=0) return 0;long long answer=0;
    for(long long place=1;;place*=10){
        long long high=n/place/10,current=n/place%10,low=n%place;
        long long full=(high%MOD)*45%MOD*(place%MOD)%MOD;
        long long partial=current*(current-1)/2*(place%MOD)%MOD;
        long long tail=current*((low+1)%MOD)%MOD;
        answer=(answer+full+partial+tail)%MOD;if(place>n/10) break;
    }
    return answer;
}
'''
CODE['P4999']=r'''int t;cin>>t;while(t--){long long l,r;cin>>l>>r;cout<<(prefix(r)-prefix(l-1)+MOD)%MOD<<'\n';}'''

CODE['P4798']=r'''
const long long MOD=1000007;int n;cin>>n;vector<int>a(n+1),before(n+1);int largest=0;
for(int i=1;i<=n;++i){cin>>a[i];before[i]=largest;largest=max(largest,a[i]);}
vector<long long>ways(n+2,1);long long answer=1;
for(int remaining=0;remaining<n;++remaining){
    int i=n-remaining;answer=(answer+(a[i]-1LL)*ways[before[i]])%MOD;
    for(int existing=0;existing<=n-remaining-2;++existing) ways[existing]=(existing*ways[existing]+ways[existing+1])%MOD;
}
cout<<answer<<'\n';
'''

CODE['UVA1640']=r'''
auto prefix=[&](long long n){
    array<long long,10>count={};if(n<=0) return count;
    for(long long place=1;place<=n;place*=10){
        long long high=n/place/10,current=n/place%10,low=n%place;
        for(int d=1;d<=9;++d){count[d]+=high*place;if(current>d) count[d]+=place;else if(current==d) count[d]+=low+1;}
        if(high>0) count[0]+=(high-1)*place+(current==0?low+1:place);
    }
    return count;
};
long long a,b;
while(cin>>a>>b&&(a||b)){
    if(a>b) swap(a,b);auto low=prefix(a-1),high=prefix(b);
    for(int d=0;d<10;++d) cout<<(d?" ":"")<<high[d]-low[d];cout<<'\n';
}
'''

CODE['CF401D']=r'''
string n;int modulus;cin>>n>>modulus;array<int,10>count={},stride={},radix={};for(char c:n) ++count[c-'0'];
int states=1;for(int d=0;d<10;++d){stride[d]=states;radix[d]=count[d]+1;states*=radix[d];}
vector<long long>dp(states*modulus);dp[0]=1;
for(int code=0;code<states;++code){
    for(int d=0;d<10;++d){
        int used=code/stride[d]%radix[d];if(used==count[d]||(code==0&&d==0)) continue;
        int next=code+stride[d];
        for(int r=0;r<modulus;++r) dp[next*modulus+(r*10+d)%modulus]+=dp[code*modulus+r];
    }
}
cout<<dp[(states-1)*modulus]<<'\n';
'''

CODE['P2518']=r'''
string n;cin>>n;long long choose[51][51]={};choose[0][0]=1;
for(int i=1;i<=50;++i) for(int j=0;j<=i;++j) choose[i][j]=(j?choose[i-1][j-1]:0)+choose[i-1][j];
array<int,10>count={};for(char c:n) ++count[c-'0'];
auto ways=[&](const array<int,10>&remaining){long long result=1;int used=0;for(int c:remaining){result*=choose[used+c][c];used+=c;}return result;};
long long answer=0;
for(int removed=1;removed<=count[0];++removed){
    auto rest=count;rest[0]-=removed;
    for(int first=1;first<=9;++first) if(rest[first]){--rest[first];answer+=ways(rest);++rest[first];}
}
for(int pos=0;pos<int(n.size());++pos){
    int current=n[pos]-'0';for(int d=(pos==0?1:0);d<current;++d) if(count[d]){--count[d];answer+=ways(count);++count[d];}
    --count[current];
}
cout<<answer<<'\n';
'''

CODE['P4124']=r'''
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
'''

CODE['P6218']=r'''
long long l,r;cin>>l>>r;if(l>r) swap(l,r);
auto prefix=[&](long long x){
    if(x<=0) return 0LL;vector<int>digits;for(;x;x>>=1) digits.push_back(x&1);reverse(digits.begin(),digits.end());
    long long memo[32][65][2];memset(memo,-1,sizeof(memo));
    function<long long(int,int,bool,bool)> dfs=[&](int pos,int balance,bool started,bool tight)->long long{
        if(pos==int(digits.size())) return started&&balance>=0;
        long long &saved=memo[pos][balance+32][started];if(!tight&&saved>=0) return saved;
        long long result=0;int limit=tight?digits[pos]:1;
        for(int d=0;d<=limit;++d){bool ns=started||d;int next=ns?balance+(d==0?1:-1):0;result+=dfs(pos+1,next,ns,tight&&d==limit);}
        if(!tight) saved=result;return result;
    };
    return dfs(0,0,false,true);
};
cout<<prefix(r)-prefix(l-1)<<'\n';
'''

DECL['SP10606']=r'''
const int STATES=59049;
int transition[STATES][10];bool valid[STATES];unsigned long long memo[21][STATES];
'''
CODE['SP10606']=r'''
array<int,10>power3;power3[0]=1;for(int d=1;d<10;++d) power3[d]=power3[d-1]*3;
for(int state=0;state<STATES;++state){
    valid[state]=state!=0;
    for(int d=0;d<10;++d){
        int count=state/power3[d]%3;
        if((d%2==0&&count==2)||(d%2==1&&count==1)) valid[state]=false;
        int next=count==1?2:1;transition[state][d]=state+(next-count)*power3[d];
    }
}
transition[0][0]=0;memset(memo,255,sizeof(memo));
auto prefix=[&](unsigned long long x){
    string digits=to_string(x);
    function<unsigned long long(int,int,bool)> dfs=[&](int pos,int state,bool tight)->unsigned long long{
        if(pos==int(digits.size())) return valid[state];int remaining=digits.size()-pos;
        auto &saved=memo[remaining][state];if(!tight&&saved!=ULLONG_MAX) return saved;
        unsigned long long answer=0;int limit=tight?digits[pos]-'0':9;
        for(int d=0;d<=limit;++d) answer+=dfs(pos+1,transition[state][d],tight&&d==limit);
        if(!tight) saved=answer;return answer;
    };
    return dfs(0,0,true);
};
int t;cin>>t;while(t--){unsigned long long a,b;cin>>a>>b;cout<<prefix(b)-prefix(a-1)<<'\n';}
'''

CODE['CF628D']=r'''
const int MOD=1000000007;int m,d;string a,b;cin>>m>>d>>a>>b;
auto prefix=[&](const string&bound){
    vector<vector<int>>dp(2,vector<int>(m));dp[1][0]=1;
    for(int pos=0;pos<int(bound.size());++pos){
        vector<vector<int>>next(2,vector<int>(m));
        for(int tight=0;tight<2;++tight) for(int r=0;r<m;++r) if(dp[tight][r]){
            int limit=tight?bound[pos]-'0':9;
            for(int digit=(pos==0?1:0);digit<=limit;++digit){
                if((pos%2==1&&digit!=d)||(pos%2==0&&digit==d)) continue;
                int nt=tight&&digit==limit,nr=(r*10+digit)%m;next[nt][nr]+=dp[tight][r];if(next[nt][nr]>=MOD) next[nt][nr]-=MOD;
            }
        }
        dp.swap(next);
    }
    return (dp[0][0]+dp[1][0])%MOD;
};
int remainder=0;bool valid=true;
for(int i=0;i<int(a.size());++i){int digit=a[i]-'0';remainder=(remainder*10+digit)%m;if((i%2==1&&digit!=d)||(i%2==0&&digit==d)) valid=false;}
int include=valid&&remainder==0;cout<<(prefix(b)-prefix(a)+include+MOD)%MOD<<'\n';
'''

CODE['CF1073E']=r'''
const long long MOD=998244353;long long l,r;int k;cin>>l>>r>>k;array<int,1024>bits={};for(int s=1;s<1024;++s) bits[s]=bits[s>>1]+(s&1);
auto prefix=[&](long long x){
    if(x<=0) return 0LL;string digits=to_string(x);vector<array<long long,2>>count(1024),sum(1024);count[0][1]=1;
    for(char c:digits){
        vector<array<long long,2>>nextCount(1024),nextSum(1024);
        for(int mask=0;mask<1024;++mask) for(int tight=0;tight<2;++tight) if(count[mask][tight]||sum[mask][tight]){
            int limit=tight?c-'0':9;
            for(int d=0;d<=limit;++d){
                int next=mask==0&&d==0?0:mask|(1<<d);if(bits[next]>k) continue;int nt=tight&&d==limit;
                nextCount[next][nt]=(nextCount[next][nt]+count[mask][tight])%MOD;
                nextSum[next][nt]=(nextSum[next][nt]+10*sum[mask][tight]+d*count[mask][tight])%MOD;
            }
        }
        count.swap(nextCount);sum.swap(nextSum);
    }
    long long answer=0;for(auto value:sum) answer=(answer+value[0]+value[1])%MOD;return answer;
};
cout<<(prefix(r)-prefix(l-1)+MOD)%MOD<<'\n';
'''

DECL['P5128']=r'''
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
'''
CODE['P5128']=r'''
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
'''

DECL['P14084']=r'''
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
'''
CODE['P14084']=r'''
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
'''

CODE['P4127']=r'''
long long low,high;cin>>low>>high;string a=to_string(low-1),b=to_string(high);int digits=b.size();
vector<int>left(digits),right(digits);for(int i=0;i<int(a.size());++i) left[digits-a.size()+i]=a[i]-'0';for(int i=0;i<digits;++i) right[i]=b[i]-'0';
long long answer=0;
for(int target=1;target<=9*digits;++target){
    int width=target+1,layer=width*target;
    vector<long long>ways(digits*layer);ways[0]=1;
    vector<array<int,10>>nextRemainder(target);for(int r=0;r<target;++r) for(int d=0;d<10;++d) nextRemainder[r][d]=(r*10+d)%target;
    vector<int>power10(digits,1%target);for(int len=1;len<digits;++len) power10[len]=power10[len-1]*10%target;
    for(int len=0;len+1<digits;++len){
        for(int sum=0;sum<=min(target,9*len);++sum) for(int r=0;r<target;++r){
            long long count=ways[len*layer+sum*target+r];if(!count) continue;
            for(int d=0;d<=9&&sum+d<=target;++d) ways[(len+1)*layer+(sum+d)*target+nextRemainder[r][d]]+=count;
        }
    }
    auto prefix=[&](const vector<int>&bound){
        long long count=0;int sum=0,remainder=0;
        for(int pos=0;pos<digits;++pos){
            int len=digits-pos-1;
            for(int d=0;d<bound[pos];++d){
                int need=target-sum-d;if(need<0||need>9*len) continue;
                int head=nextRemainder[remainder][d];int tail=(target-head*power10[len]%target)%target;
                count+=ways[len*layer+need*target+tail];
            }
            sum+=bound[pos];remainder=nextRemainder[remainder][bound[pos]];if(sum>target) return count;
        }
        return count+(sum==target&&remainder==0);
    };
    answer+=prefix(right)-prefix(left);
}
cout<<answer<<'\n';
'''

DECL['UVA1652']=r'''
long long ways[81][2],ones[81][2];
long long firstOnes(int len,int previous,long long count){
    if(len==0||count==0) return 0;
    long long zero=ways[len-1][0];
    if(previous==1||count<=zero) return firstOnes(len-1,0,count);
    return ones[len-1][0]+(count-zero)+firstOnes(len-1,1,count-zero);
}
'''
CODE['UVA1652']=r'''
ways[0][0]=ways[0][1]=1;
for(int len=1;len<=80;++len) for(int previous=0;previous<2;++previous){
    ways[len][previous]=ways[len-1][0];ones[len][previous]=ones[len-1][0];
    if(previous==0){ways[len][previous]+=ways[len-1][1];ones[len][previous]+=ones[len-1][1]+ways[len-1][1];}
}
long long n;
while(cin>>n){
    long long answer=0;int length=1;
    while(n>=length*ways[length-1][1]){
        n-=length*ways[length-1][1];answer+=ways[length-1][1]+ones[length-1][1];++length;
    }
    long long full=n/length,rank=full;int rest=n%length;
    answer+=full+firstOnes(length-1,1,full);
    if(rest>0){
        ++answer;--rest;int previous=1;
        for(int remaining=length-1;rest>0;--remaining,--rest){
            long long zero=ways[remaining-1][0];int bit=0;
            if(previous==0&&rank>=zero){rank-=zero;bit=1;++answer;}
            previous=bit;
        }
    }
    cout<<answer<<'\n';
}
'''


from core7_authoring import add
A=['io-basics','basic-control','vector','integer','functions']
D=A+['dp','digit-dp']

def emit(pid,title,meaning,brief,detail,pitfalls,complexity,tags,lessons):
    add(pid,title,meaning,brief,detail,CODE[pid],pitfalls,complexity,tags=tags,lessons=lessons,declarations=DECL.get(pid,''))

emit('P2657','记住前一位，逐位统计满足相邻差的正整数',
    '统计闭区间内不含前导零、且相邻十进制数字之差的绝对值至少为二的正整数。',
    r'''先求不超过x的合格正整数数目F(x)，答案为F(b)减F(a减一)。从高位向低位填，状态只需位置、前一实际数字和是否贴着上界。用十表示还没开始，前导补零不参与相邻比较；一旦开始，每个新数字与前一位差至少二。末尾仍没开始的全零路径不计数，只缓存已经小于上界的状态。''',
    r'''直接枚举区间会遇到二十亿个数，但一个前缀能不能继续，只取决于最后一位。例如已经写到三，下一位只能选零、一、五至九；更早的数字不再影响这一次相邻比较。

定义F(x)为一到x中的合格数数目，F(零)为零。闭区间分成一到b减去一到a减一，端点a因此仍会保留。

将x写成十进制字符串，从左向右填相同宽度的数。状态previous为零至九时表示最后一个真实数字；十是独立的“还没开始”标记。初始previous为十。还没开始时填零，仍保持十；填一个非零数字才开始。这样较短的数会恰好对应一条前导补零路径，不会出现重复表示。

已经开始以后，零就是普通数码，也要与前一位比较。比如一百的末尾有两个相邻零，不能因为它们为零就跳过；而用统一宽度表示七时，前面的占位零不能拿来与七比较。

tight表示已填前缀与x完全相同。贴界时当前最多填x本位，不贴界时最多九；选了更小数字就永久离开上界。只把不贴界的结果按位置与previous记忆，因为它的剩余选择不依赖x的后续字符。

到达末尾时，previous不为十就贡献一，否则只是零，贡献零。每个正整数有唯一十进制表示，递归逐位枚举不漏不重；每一步又都检查了新产生的相邻对，所以留下的恰好是合格正整数。

两个前缀函数各自清空缓存，不能把另一个上界的位置定义混进来。虽然本题最终计数不超过二十亿，统一用long long保存计数与区间差。''',
    '相邻差取绝对值；零开始后是实际数字；前导占位零不比较；排除零本身；闭区间减a减一；两个上界分别重建缓存。',
    r'设十进制位数为D，时间 $O(100D)$，空间 $O(10D)$。',['数位 DP'],D+['recursion','lambda-local'])

emit('P14074','同时保存方案数与数值和，只保留二进制奇数个一',
    '求区间中二进制表示里一的数量为奇数的所有整数之和，不是求这些数的数位和。',
    r'''二进制逐位填上界以内的数，状态记上界关系与已填一的个数奇偶。每格同时存数量C和这些前缀的数值和S；接上位d后，新数值总和为二乘S加d乘C，奇偶再异或d。前导零不改变奇偶或数值，末尾只取奇数状态。用两个前缀和相减，全部运算用六十四位。''',
    r'''三至八之间，二进制里有奇数个一的是四、七、八，要求相加得到十九。统计个数会得到三，统计这些数的一的数量也不会得到十九；本题累加的是整数本身。

令F(x)为零至x中一的数量为奇数的整数的数值和，答案是F(r)减F(l减一)。零的奇偶为偶，因此即使统一枚举包含零，也不会贡献答案。

逐位处理二进制。未来判断只需要已填一的数量的奇偶，不需要保存完整个数。另用tight表示是否仍与上界前缀相等。

同一状态里可能汇入很多前缀。保存C表示有多少个，S表示它们的数值总和。给每个前缀v接上一位d，新值为二乘v加d，所以全部新值之和为：

$$S'=2S+dC.$$

数量仍增加C；若d为一，奇偶翻转，若为零则不变。必须同时保存数量，否则不知道新末位d需要加多少次。这里乘二的是原来的数值和；如果累加的是各位数字之和，就没有这个乘二，独立基础课对照解释两种量。

处理零至三十位，共三十一位，足以覆盖十亿。前导零既不增加一的个数，也不改变数值，所以这里不用额外的是否开始标记。每轮从旧表转移到清零的新表，结束后只相加奇数奇偶下的贴界与不贴界两格。

所有被统计值都不超过十亿，总和不超过一到十亿的总和，long long足够；不能用int保存前缀总和。F对负数返回零，使通用的区间前缀写法也有清楚边界。''',
    '求整数之和；接二进制位时旧数值乘二；新位要乘方案数；奇偶只由位一翻转；每轮重建表；总和用六十四位。',
    r'设二进制位数为D，时间 $O(D)$，额外空间 $O(1)$。',['数位 DP'],D+['bitwise','digit-aggregation'])

POSITION_DETAIL=r'''按某个十进制位置单独统计贡献。设它的位权为p，把上界n分成高位high、当前位cur和低位low。例如n为三千四百五十六、p为一百时，三者分别为三、四、五十六。

从零写到n，当前位每经历一个完整的十乘p长周期，零至九各出现p次，数字总和贡献是四十五乘p。完整周期有high个。

最后一个不完整周期中，小于cur的零至cur减一都各出现p次，其数字之和为cur乘cur减一除二，再乘p；当前数字cur只出现low加一次。

因此本位贡献可以分成三段相加：

$$high\cdot45p,$$

$$\frac{cur(cur-1)}2\,p,$$

$$cur(low+1).$$

各个位置独立相加，因为一个数的数位和本来就是所有位置数码之和。统一宽度中增加的前导零贡献零，数零本身也贡献零，因此不用像统计零出现次数那样减掉占位零。

代码用n除p再除十得到high，分别用n除p模十与n模p求cur、low。这样不需要先构造十乘p。处理完本位后，若p已经大于n除十便结束，再乘十就只会多出一个无用位置。'''

emit('P1836','按十进制位置统计完整周期与最后一段',
    '书页从一编到n，求全部页码中各个十进制数字的总和，n至多十亿。',
    r'''逐个十进制位置看数字零至九的循环。位权p处，高位high带来high乘四十五乘p，当前位cur以前的整段带来cur乘cur减一除二再乘p，当前数字还出现低位low加一次。把三段贡献以及所有位置相加。前导零贡献零，可自然包含数零；总和用long long。''',
    POSITION_DETAIL+r'''

例如页码一至十三，个位的一到九贡献四十五，十至十三的个位再贡献六；十位的一在十至十三中出现四次，总和五十五。这里没有把十三看作一个不可拆的数值。

n至多十亿，结果的量级为位数乘n乘九，六十四位足够。每个算式的操作数也要先使用long long，不能等int乘法溢出后才赋给大类型。''',
    '求页码数字之和；四十五是一轮零至九的数字和；当前段低位加一；前导零本题贡献零；不是统计出现次数也不是累加页码数值。',
    r'时间 $O(\log n)$，额外空间 $O(1)$。',['组合计数'],A+['counting'])

emit('P4999','用位置贡献求区间数位和，每一段先取模',
    '多组询问，求闭区间内所有整数的十进制数位和之和，答案模十的九次方加七，端点可达十的十八次方。',
    r'''答案是F(r)减F(l减一)，F按十进制位置把完整周期、当前位以前的整段、最后低位段的数位贡献相加。范围很大，真实数位和可能超出六十四位；把high、位权p先取模后再相乘，而不是先算完整乘积。低位加一也单独取模，区间差规范到非负。''',
    POSITION_DETAIL+r'''

区间使用同一个前缀函数相减。本题端点可到十的十八次方，真实总和可超过long long，不能把小范围的完整乘积原样计算后才模。

模数为十的九次方加七。完整周期先算high模模数，再乘四十五并取模，然后乘p的余数；两个模后乘数的乘积在六十四位内。部分整段的cur乘cur减一除二只有零至三十六，先做精确整数除二，再与p的余数相乘。最后cur乘low加一的余数同样安全。

最高位p可能已经是一后面十八个零。如果直接写十乘p判断下一位置，乘法会超出六十四位；代码用p大于n除十作为结束条件，并用n除p再除十求high。

前缀差可能为负，先加一次模数再取模。每次询问独立处理两端，F(零)返回零。这里模的是结果，不能把原上界先模后再统计数位。''',
    '模数为十的九次方加七；真实总和可能超六十四位；每段先模再乘；整数除二先完成；最高位不计算十乘p；不能先缩小原上界。',
    r'每组时间 $O(\log r)$，额外空间 $O(1)$。',['组合计数'],A+['counting','modular'])

emit('SP17247','把区间数位和拆为两个精确的位置贡献前缀',
    '多组区间，求所有整数的十进制各位数字之和的总和，端点可为零且至多十的十五次方，不取模。',
    r'''先求零到n的数位和F(n)。每一位按完整十数循环与最后不足一轮分成三段，得到high乘四十五乘p、cur乘cur减一除二再乘p、cur乘low加一。区间用F(b)减F(a减一)，n非正时前缀贡献零。零的数位和本就是零，全程long long精确保存，不加取模。''',
    POSITION_DETAIL+r'''

输出要求精确整数，没有指定任何模数。端点至多十的十五次方，最多十六位，所有数位贡献之和仍小于六十四位上限，所以直接使用long long。

区间二十八至三十一中，四个数的数位和分别为十、十一、三、四，答案二十八；这与这四个整数相加完全不同。

输入可能从零开始。把F(n)在n非正时定义为零，则a为零时需要的F(负一)也可直接返回零。数零自身的数字和为零，是否把它包含进前缀不会改变结果。

输入先给询问组数，每组打印独立一行。程序逐位循环只保留当前位置和累计答案，不需要建立按上界大小的数组。''',
    '本题不取模；零的数位和为零；a可为零而a减一为负；答案不是整数之和；当前位尾段包含端点所以加一；使用六十四位。',
    r'每组时间 $O(\log b)$，额外空间 $O(1)$。',['组合计数'],A+['counting'])

emit('P4798','按第一次不同的位置计排名，滚动保存剩余队伍方案',
    '合法队伍编号按首次出现顺序从一递增，给定长度至多一万的合法编号序列，求它的字典序排名，第一名记一，模一百万零七。',
    r'''若当前位置首次比给定序列小，可选一到a本位减一，恰有a本位减一个旧队伍编号，选择后已有队伍数不变。令F(r,k)表示还剩r人、已有k队的方案数：下一人选k个旧队之一或唯一的新队，故为k乘F(r减一,k)加F(r减一,k加一)。按剩余长度递增滚动，累加每个首次变小位置的贡献，再加一。''',
    r'''[CEOI原题](https://ceoi2015.fi.muni.cz/day1/eng/day1task2-eng.pdf)的队伍按队长姓名排序，玩家也按姓名排列。因此编号一首先出现，编号二只能在已有一以后首次出现，之后同理。若前缀最大编号为k，下一项只能为一至k加一；它不是任意的一至n排列。

按字典序计排名，可以把所有更小序列按“第一次与输入不同的位置”分类。设这一位输入为a，前面完全相同时已有k队。更小的数字一至a减一全部不超过k，因为输入保证a不超过k加一。因此恰有a减一个选择，每一个都只是加入旧队，不改变已有队伍数k。

令F(r,k)为剩下r个玩家、已有k个队时的合法补全数。没有剩余玩家时只有空补全，F(零,k)为一。下一人加入旧队有k种选择，之后仍是k队；开新队只有唯一编号k加一，之后是k加一队。所以：

$$F(r,k)=kF(r-1,k)+F(r-1,k+1).$$

该位置的贡献为a减一乘F(n减i,k)。各组第一次不同位置互不相交，加完再加一，就是从一开始的排名。例如三人的序列依次为111、112、121、122、123，122排第四。

n可达一万，完整二维表太大。先保存每个位置之前的最大编号。再令r从零递增，相应要查询的位置i从最后向前移动，每次只查询当前行的一个k。旧行不再需要，可以滚动为一行。

更新F的新一行要使用旧行的k与k加一。代码让k从小到大，尚未改写的k加一仍为旧值；如果倒序就会混入新行。只更新下一次可能用到的k范围，每次上界缩小一，边界的更大旧值不被提前丢弃。

模数是一百万零七，即1000007，不能写成常见的十的九次方加七。这里只有加法乘法，不需要判断模数是否为质数，也不使用除法逆元。''',
    '合法序列按首次出现编号；首次变小的选择全是旧队；排名加一；模数1000007；滚动时k递增以读旧的k加一；原题保证输入合法。',
    r'时间 $O(n^2)$，空间 $O(n)$。',['组合计数','线性 DP'],A+['dp','counting','modular'])

emit('UVA1640','逐位数零至九的出现次数，单独去掉前导零',
    '反复读入两个正整数，统计两者之间所有数中零至九各出现多少次；端点可逆序，零零终止。',
    r'''对每个数字分别求一到n的出现次数前缀，区间相减。非零数字在位权p处有high个完整周期，再按当前位是否大于或等于它加最后一段。零不能数前导补位：只有high为正时才统计，完整部分由high减一个周期，再接当前段。先交换逆序端点，终止行不处理。''',
    r'''[原始PDF](https://onlinejudge.org/external/16/1640.pdf)说明端点都是正整数、小于一亿，可有五百组，零零是终止符；并没有保证第一个端点较小。程序先交换逆序端点，再计算两个前缀数组的差。

选定十进制位置p，把n分成high、当前数码cur、low。对非零数字d，每个完整周期出现p次，先加high乘p。最后不足一轮的段中，若cur大于d，d又完整出现p次；若cur等于d，只出现low加一次；若cur小于d，不增加。

数字零必须单独处理。如果把小数补成统一宽度，例如把七写成007，补上的两个零不属于原数。恰好需要去掉最高部分为零的那一个完整周期，所以零的完整部分为high减一乘p，而且必须先检查high大于零。

high大于零时，若当前数码为零，尾段再加low加一次；否则当前零段已经走完，加p。high为零时，该位置尚未真正出现在那些短数里，对零贡献一律为零。

例如统计一至十三，十的个位提供一个真实零；一至九前面的占位零一个也不能加。数一百的个位与十位则确实各有一个零，两个位置要分别计数。

这里要输出十个数字出现次数，不是把数字乘次数后再求和。用array保存零至九的结果，按固定顺序输出，数字间一个空格。前缀n非正时返回全零数组；因此较小端点为一时不需要特殊分支。''',
    '输入端点可能逆序；零零只终止；正整数区间不包含数零；前导补位零不计；十个计数依次输出；不能把次数替换为数位和。',
    r'每组时间 $O(10\log b)$，额外空间 $O(10)$。',['组合计数'],A+['standard-array','counting'])

emit('CF401D','按每种数字已使用数量建状态，重复数字不编号',
    '把n的全部十进制数字重排成不含前导零的不同整数，统计能被给定模数整除的个数。',
    r'''同一种数字的多个副本不能按下标计成不同排列。用十个已使用次数描述前缀，每个次数按原出现次数加一作为进位基数，编码成一个整数。状态再记当前余数，追加可用数字d后次数加一、余数变为十乘旧余数加d取模。初始不能放零，最终取全部次数用完且余数零的格。''',
    r'''例如223中的两个二不可区分。若给每一位编号再按下标排列，两个二交换会产生相同整数并重复计数。可以直接记录每种数码使用了几次，从状态层面消除这种重复。

设原数中d出现c[d]次，对应使用次数u[d]取零至c[d]。将这十个小计数编码为混合进制整数：第d项的基数是c[d]加一，stride[d]为前面各个基数的乘积。编码是所有u[d]乘stride[d]之和。

编码除stride[d]再模该项基数，可以取出u[d]。若尚未用满d，追加它只需给编码加stride[d]；因为检查过没有用满，不会错误进位到下一项。最终全部用满的编码恰为总状态数减一。

再保存当前数值对m的余数r。接上d后，新余数为十乘r加d再模m。每个可用数码只转移一次，不乘剩余副本数；那些副本相同，不是不同选择。

编码每次严格增加，因此按编码从小到大更新即可。只有编码零表示空前缀，此时不允许追加零；非空前缀中的零都正常参与数值和余数。

本题n不超过十的十八次方。十八位时十个计数基数的乘积最多26244；唯一可能的十九位输入是一后面十八个零，它的状态更少。这样比按十八个位置建立大掩码表更省空间。每种排列都有唯一的数码选择路径，最终计数不重复；十八位的排列数不超过十八的阶乘，long long足够。''',
    '重复数字不编号也不乘剩余副本数；首位不能零；次数未满才加stride；余数按十进制追加；结果是不同整数个数；十九位上界要能以字符串读入。',
    r'设状态数 $S=\prod_{d=0}^9(c_d+1)$，时间 $O(10mS)$，空间 $O(mS)$。',['数位 DP','状压 DP'],D+['strings','counting','modular'])

emit('P2518','按删零后的长度分类，再数第一次更小的数码',
    '给定至多五十位的非负整数，可删去任意多个零并重排其余全部数字，统计比原数小的不同整数；不允许前导零，保证答案不超有符号六十四位。',
    r'''删去不同个数的零会得到不同长度。对所有较短长度，先固定非零首位，再按剩余各数字个数算多重集合排列；相同副本不区分。长度不变时沿原数扫描，枚举第一次变小的可用数码，剩余任意排列。排列数用逐类插入的组合数乘积计算，避免五十阶乘；只计算实际计入答案的分支。''',
    r'''本题允许丢掉零，不能只统计原长度的重排；其它非零数码必须全部留下。例如1020还可删零得到12、21等短数，完整答案共有七个。

先按删去零的个数分类。删一个至全部原零，每个类别长度都比原数短。较短的合法正整数必然小于原数，因此先枚举非零首位，移去这一枚，再统计余下数码的不同排列。首位相同的同类副本不区分，不能乘它的出现次数。

如何求剩余多重集合的排列数？已放入used个数码，接着插入c个相同新数码，只需选择used加c个位置中的c个。把十类依次插入，将这些组合数相乘，就是多项式系数。预先用帕斯卡递推计算五十以内的组合数，不计算五十阶乘，也不通过大阶乘相除。

没有删零时长度与原数相等。沿原数逐位扫描，当前之前的前缀都与原数相同；试放一个比原位小的可用数码，首位仍禁止零，之后任意补全都更小。把这些补全计入，再消耗原位数码继续走相等分支。最后不把原数自身加入。

每个更小同长数都有唯一的第一次变小位置，每个短数有唯一的删零数量和首位，因此这些类别互不重叠。同种零删掉哪一枚不会产生新类别。

五十位原数不能读入long long，原数本身只用字符串比较路径。组合数最大为五十取二十五，仍在六十四位内。多项式系数虽然一般可能很大，本程序只在已经固定合法更小前缀或合法短数首位以后调用；这一个分支的全部结果都是答案的子集，所以按题目保证不会超过六十四位。乘积因子均至少一，中间乘积也不会超过该分支最终值。

这条范围保证依赖“先固定合法首位再算”。不能先计算包含前导零的庞大总排列再相减，因为那两个中间量不受答案上限保护。数零本身没有更小的非负结果，程序自然输出零。''',
    '只允许删零；非零副本全部保留；同类数字不区分；短数也要禁止前导零；不包含原数；先固定合法前缀才使用答案范围保证；不用大阶乘相除。',
    r'设长度为D，预处理与统计时间 $O(D^2+100D)$，空间 $O(D^2)$。',['组合计数'],A+['strings','counting'])

emit('P4124','把相邻重复长度、出现过三连与四八标记分开记',
    '统计十一位无前导零手机号，要求出现至少三个相邻相同数字，并且不能同时出现四和八。',
    r'''固定十一位从高到低填，首位只能一至九。状态保存前一个数字、末尾连续相同长度（封顶三）、是否已经出现过三连、四八出现掩码和上界关系。新数字更新这些量，四和八同时出现就丢弃；末尾只要求曾有三连，不要求三连正好在末尾。前缀F(R)减F(L减一)，短于十一位的前缀为零。''',
    r'''两个限制都与已填前缀有关，但所需信息不同。判断下一位能否形成三连，只需要前一个数字和当前相同后缀长度；判断整串是否曾经成功，则必须另记found，不能在换数字后把已经发生的三连忘掉。

状态run表示末尾连续相同数字有几位，达到三以后封顶三。接同一个数字便增加并封顶，接不同数字则回到一。新run为三时，把found永久设为真。比如14444101000有两处三连，中间换了很多数字，仍然满足条件。

四和八的条件另用两位掩码：一位表示见过四，另一位表示见过八。两位都为一时直接拒绝。它不禁止四，也不禁止八，只禁止两者在同一号码里同时出现；重复很多个四本身可以合法。

本题号码长度固定为十一位，首位只能一至九，其余位置零至九。这里不能允许前导占位零后把短数也加入，因为运营商只发行题目指定长度的号码。

tight仍表示与上界前缀相等。不贴界的状态按位置、前一位、run、found、四八掩码缓存。结束时返回found；其它限制已经在转移中维护，不需要重新扫描号码。

F(x)统计不超过x的合格十一位号码。若x小于十的十次方，直接为零。这一点用于L恰好等于最小十一位数时，L减一已只有十位；不能仍用它的短字符串硬取十一位。

答案最多是全部十一位正整数数量，long long足够。两次前缀各自重建缓存，不把R的tight条件带入L减一。''',
    '固定十一位；首位非零；三连出现后永久保留；run封顶三即可；四和八各自可出现；两者同时出现才拒绝；下界减一可能短一位。',
    r'设长度为D、数码数为十，时间 $O(D\cdot10\cdot4\cdot2\cdot4\cdot10)$，空间为同一状态量级去掉最后一个枚举十。',['数位 DP'],D+['bitwise','recursion','lambda-local'])

emit('P4127','枚举最终数位和，用后缀和与余数表补全上界',
    '统计区间内能被自身十进制数位和整除的正整数，端点可达十的十八次方。',
    r'''先枚举最终数位和s，使“模自身数位和”变成模固定s。预处理ways[len][sum][r]：长len的可含前导零后缀，数位和sum、余数r的个数。扫描每个上界的第一次变小位，已定前缀v、数位和h后，查询剩余和s减h以及余数负v乘十的剩余位次方。两端共用同一张后缀表，最后相减。''',
    r'''不能直接把当前前缀的数位和当模数，因为未来加数码会改变它，之前保存的余数就失去意义。最终数位和却只在一至九乘总位数之间，可以先枚举它为固定的s。

固定s后，定义ways[len][sum][r]：恰好len位的字符串，允许前导零，数位和为sum，作为整数模s为r的数量。初始空串只有和零、余数零的一种。接上数字d，和增加d，余数变为十乘r加d再模s。只保存和不超过s的状态。

现在统计不超过一个上界x的数。把它补成与R相同的宽度，从左向右走相等前缀；在某位选更小数码后，后面就可任意填。

设这个较小前缀的余数为v、数位和为h，后面剩len位，后缀余数为r。整数余数是：

$$v10^{len}+r\pmod s.$$

因此需要的后缀余数是负v乘十的len次方模s，后缀数位和是s减h。直接查对应表格；和为负或超出九乘len时不可能，跳过。相等路径走完后，若它本身的数位和恰为s且余数为零，再加一。

同一个固定s的后缀表与具体上界无关，所以R与L减一共同使用它，再把前缀计数相减。每个整数只有唯一的实际数位和，只会被一个s计入；数零的和为零，而s从一开始，因此不会误计零。

十的十八次方是十九位，代码按真实位数设置九乘D的上界，不能固定认为最多十八位。查询中的最长自由后缀仍只有十八位，各表项不超过十的十八次方，六十四位可精确保存。每轮只保留一个s的表，控制内存；余数转移与十的幂余数先预处理，避免最内层反复求余数。

枚举s带来的复杂度要如实计入，不能只写成普通数位DP的位数乘状态常数。''',
    '先固定最终数位和再取模；十九位上界；数零不计；补零不改变数位和；前缀与后缀通过十的幂合成余数；同一s表供两端共用；六十四位计数。',
    r'设D为位数、S为九乘D，时间 $O(10D\sum_{s=1}^{S}s^2)$，空间 $O(DS^2)$。',['数位 DP'],D+['modular','counting'])

emit('P5128','按最长段的阈值累加，用后两位批量更新等差后缀',
    '把一至n写成k进制，求每个表示中最长连续等差数码段的长度之和，模19260821；n可达k的十八次方。',
    r'''一位数至少贡献一，其余至少贡献二。对每个阈值t从三至总位数，再加“最长段至少t”的个数，即n减去从未形成t长段的数目。后者逐位DP，保存最后两数码与当前等差后缀长度。只有新位等于二乘末位减前位才延长，其它选择都回到长度二；先按末位汇总统一重置，再把唯一延长选择挪回。上界用字符串除k转换，不依赖六十四位。''',
    r'''两个数码总能构成等差段，三个起才真正限制公差；公差可以为负或为零。比如数码一三五二零的最长等差段是一三五，长三，不能把整个整数的连续数值当作数码序列。

对一个长度至少二、最大等差段长为v的数，可以先计二，再对每个t从三至v各加一。因此总答案先放二乘n，减去只有一位的数的个数，然后对每个t增加满足最大段至少t的整数数目。

把后一个数量写成n减avoid(t)。avoid(t)统计一至n中，从未出现长度t等差段的数。这样单次DP不必同时记录历史最大值，只需保证后缀从未碰到阈值。

长度至少二的前缀，用a、b表示最后两位，run表示当前最长等差后缀长度，始终小于t。接c时，若c减b等于b减a，run增加一；否则最后两位b、c仍构成等差段，新run是二。达到t就拒绝。

若对每个状态再枚举全部k种c，会多一个k因子。观察每组a、b只有唯一可能延长的c，即二乘b减a。先把所有以b结束的前缀数量按b汇总，给每个c统一放到新run为二的格子；再对每个旧状态，把那个唯一延长选择从默认的二中减掉，转放到run加一。若延长后达到t，只减不加；若c不在零至k减一内，所有选择确实都会重置，不用调整。

尚未开始与只有一位的前缀单独存放。前导占位零不构成真实等差段，实际开始后才记录第一位、第二位。已经小于上界的状态做上述批量转移；贴界的路径只有一条，逐一试本位更小数码注入普通状态，再沿相等数码继续。一旦贴界路径违反阈值便停止注入，但其它已离界状态仍继续。

n是十进制输入，最大约为一后面三十二个零，不能读入long long。用十进制字符串反复除k：从左到右携带余数，把每位的十乘余数加数码除k，得到商串与一个k进制余数。余数倒序后就是上界各位。商的单个数码始终在零至九，不会因为k大于十就改变十进制存储方式。

n恰为k的十八次方时表示有十九位，阈值也要覆盖十九。n本身只需另外逐字取模以参与答案，不转成机器整数。所有计数在19260821下加减规范化，不使用除法或逆元。''',
    '数码连续子串；公差可负可零；两位总是等差段；改变公差后后缀长二；延长达到阈值要拒绝；前导零不成段；n可超六十四位；最高有十九位。',
    r'设k进制位数为D、十进制输入长度为E，时间 $O(k^2D^3+ED)$，空间 $O(k^2D+E)$。',['数位 DP'],D+['strings','counting','modular'])

emit('P6218','只对实际二进制位累计零减一的差',
    '统计区间内二进制表示中零的个数不小于一的个数的正整数。',
    r'''前缀F(x)逐位填二进制，状态保存零数减一数的balance、是否已经开始和上界关系。尚未开始时填零只是占位，不增加balance；真实首位必为一，开始后零加一、一减一。末尾只统计已经开始且balance非负的路径。两端前缀相减，不能把短数补在前面的零算进去。''',
    r'''九的二进制是1001，零和一各两个，满足条件。一的表示只有1，没有零；若把它补成0001再数零，就会得到错误结论。因此是否已经出现真实首位必须进入状态。

把零的数量减一的数量记为balance，最终要求balance不小于零。接一个真实零时差增加一，接真实一时差减少一；只保存这个差足以判断所有未来补全，不必分开存两个计数。

started为假时，填零仍未开始，balance保持零；填一开始表示并把差变为负一。started为真后，所有零都是实际位，都参与统计。

tight控制本位是否受上界限制。不贴界状态按位置、balance与started记忆。balance可能为负，数组下标统一加三十二；本题上界至多二十亿，最多三十一位，偏移后的范围足够。

结束时要同时要求started为真，排除全占位零路径，因为圆数定义为正整数。使用F(r)减F(l减一)，非正前缀直接返回零；若端点逆序先交换，也不影响正常有序输入。

每个数的二进制表示唯一，转移正好累计它所有实际位的零一差，因此末尾判定与题意等价。计数用long long保存，两个上界分别清空缓存。''',
    '只数实际二进制位；零本身不是正整数；短数前面的补零不增加零数；相等也满足；balance可负需偏移；闭区间前缀减下界减一。',
    r'设二进制位数为D，时间 $O(D^2)$，空间 $O(D^2)$。',['数位 DP'],D+['bitwise','recursion','lambda-local'])

emit('P14084','按整段的一的个数转移，再求线性递推的远项',
    '将长度n的二进制串l重复k次作上界，统计不超过它且每相邻两段的一的总数不超m的串，模998244353，k可达十的十八次方。',
    r'''先求a[j]为任意n位段恰有j个一的数量，b[j]为小于l且有j个一的数量。保存已经小于上界时末段的一数分布，另存完全贴界的一条路径。普通转移用前缀和满足前段一数加j不超m，贴界转普通再乘b[j]，还要检查原段一数加j。第一段没有前驱限制。此后是n加二维的固定线性转移，生成两倍维数个答案，用BM找递推、多项式快速幂求第k段。''',
    r'''不能展开k个l，k可达十的十八次方。先把逐位限制改成整段限制。任何n位串中一的数量为j时有a[j]种，即n取j；后续与它相邻的段只关心j，不关心具体排列。

还需要处理不超过重复串的条件。整段比较时，只有“已经小于上界”与“仍完全相同”两类。设b[j]为严格小于l且有j个一的n位串数量，c为l的一数。

预处理b时枚举第一次比l小的位：原位必须是一，改成零；之前的一数固定，后面若还需要若干个一，就选对应数量的位置。因此用组合数即可累计所有j，不必枚举二的n次方个段。

第一段没有前一段，离界分布直接初始化为b，贴界路径为一。之后设x[j]为已经离界、末段有j个一的数量，t为贴界路径是否仍合法。新的一数j从普通状态获得：

$$a[j]\sum_{i=0}^{\min(n,m-j)}x[i].$$

上界小于零时这项为零。给x做一次前缀和，就能在线性时间求所有j。贴界转为离界还可增加t乘b[j]，但必须满足c加j不超m，因为它前面那一段恰为l。新的贴界路径则只有在二乘c不超m时保留。

所以从第二段开始，向量x的n加一格与t这一格通过同一个固定线性变换更新，维数d为n加二。答案S也是这个向量各格之和。由有限维线性变换的特征多项式恒等式，S必满足阶数不超过d的线性递推，不能在没有这种阶数依据时凭少量项猜规律。

生成S的一至二d项只需二d轮前缀和转移。然后用Berlekamp–Massey算法恢复递推系数，再把幂指数按递推多项式约简，求S的第k项。两项通用算法的失配修正、逆元、系数顺序及多项式约简均在独立基础课给出完整例程；这里使用的是下标从零的数组，第一项S一存下标零，最终指数为k减一。

模数998244353为质数，BM中出现的非零失配才可取逆元。第一段单独初始化尤其关键：即使c加c不合格，首段等于l也可能在第二段转成更小的合法串，不能提前抹掉初始贴界路径。

复杂度包含BM和递推快速幂，用前缀和生成初值后不必做n立方乘logk次的稠密矩阵乘法。全零串、m为零、原重复串自身是否合法，都由统一转移处理。''',
    '串可含前导零且长度固定；第一段没有前驱；小于l不代表相邻限制消失；贴界转离界仍检查c加j；相等串也计；须先证明递推阶数界；数组下标对应k减一。',
    r'时间 $O(n^2\log k+n\log P)$，空间 $O(n^2)$，P为质数模数；第二项包含BM失配求逆。',['数位 DP','递推'],D+['strings','counting','modular','linear-recurrence'])

emit('SP10606','三进制记录每个数码未出现、正奇次与正偶次',
    '统计区间内正整数：实际出现的偶数数码各出现奇数次，实际出现的奇数数码各出现偶数次，端点可达十的十九次方。',
    r'''每个数码要区分未出现、正奇次、正偶次三态，追加时依次零到一、一到二、二到一，用十位三进制编码。状态零独作尚未开始，前导零保持零，其后真实零按普通数码更新。末尾偶数数码允许未出现或奇次，奇数数码允许未出现或偶次，排除全未开始。用无符号六十四位处理十的十九次方，缓存按剩余位数跨询问复用。''',
    r'''题意只约束出现过的数码，不要求十种数码全出现。例如七十七合格，因为七出现两次；没有出现的零、二等不会导致不合格。数码零是偶数，实际零出现后同样必须是奇数次。

只记出现次数奇偶还不够：零次与正偶次都为偶，但对偶数数码，零次允许，正偶次不允许。因此为每个数码保存三种状态：零表示未出现，一表示正奇次，二表示正偶次。

追加该数码后，变化为零到一、一到二、二到一。十个三态用三进制编码，总状态数为三的十次方。预处理每个编码追加零至九后的目标编码，再预处理该编码是否满足最终条件。

偶数数码的最终状态不能是二；奇数数码的最终状态不能是一。由于一、二之间切换永远不会回到零，整个编码零恰好可以表示还没开始。此时追加占位零继续保留编码零；任何非零首位开始后，后面的零都照正常三态更新。

逐位受上界限制，离界结果按剩余位数与编码缓存。剩余位数的意义独立于某个上界的总长度，所以多组询问可以复用同一张表；贴界路径不缓存。末尾全零编码返回假，排除整数零。

端点可为十的十九次方，超过有符号long long上限，但小于无符号六十四位上限。输入、计数和区间差都使用unsigned long long；A至少一，所以A减一不会下溢。

最长输入有二十位，不过它只能是一后面十九个零；第一次离开上界后，自由后缀最多十九位，任一缓存计数不超过十的十九次方，无符号六十四位可保存。初始化缓存用全一位模式表示未计算，与所有合法计数区别开；它不是“计算得到的零”。''',
    '零次与正偶次必须区别；不要求全部数码出现；零是偶数；前导零不登记；真实开始后三态永不回到全零；上界超有符号六十四位；跨询问只缓存离界状态。',
    r'预处理与首次填充时间 $O(10D3^{10})$，缓存后每次查询贴界部分 $O(10D)$，空间 $O(D3^{10})$。',['数位 DP','状压 DP'],D+['unsigned64','strings'])

emit('UVA1652','按斐波那契表示长度跳过整块，再处理最后半个数',
    '把自然数一、二、三依次写成不含相邻一的斐波那契进制表示并连接，求整个无限串前N个字符中一的数量，N至多十的十五次方。',
    r'''斐波那契表示按长度、同长字典序排列就是自然数顺序。预处理长len后缀、给定前位是否一时的合法串数量与其中一的总数。整块长度L的每个数首位一，用数量乘L扣字符，并加首位与后缀的一数。剩余字符拆成若干完整同长表示和下一表示的前几位；按零分支大小递归统计前q条后缀，再按排名解出最后前缀。''',
    r'''[原题PDF](https://onlinejudge.org/external/16/p1652.pdf)中的F零与F一均为一，表示的最低位权用F一，因此从低到高的实际位权是一、二、三、五等。合法表示不能有相邻一，数一至七分别为1、10、100、101、1000、1001、1010。询问的N是连接串字符数，不是要处理前N个自然数。

这种唯一表示按位权从高到低贪心可得。短于L位的最大数恰为第L位权减一；同长时首次不同的一位，其权重大于所有更低合法位能凑出的最大值。因此按长度递增、同长按字典序列出合法串，正好就是自然数顺序。

预处理ways[len][previous]与ones[len][previous]，分别表示还剩len位、前位为previous时的合法补全数量及这些补全里一的总次数。空后缀数量一、一数零。下一位为零时都转到previous为零；下一位为一只在previous为零时允许，此分支的一数还要为每个补全加一个当前一。

长度L的正数固定首位一，余下L减一位从previous为一开始。因此该整块有ways[L减一][一]个数，占用L乘这个数量个字符；一的总数是每个数的首位一，加上ones表里的后缀一数。整块能吃下就扣掉字符并增加答案。

到了吃不下的长度，把余下字符数分为q个完整表示和rest个字符。q个数的首位一先贡献q，再统计字典序最前q个合法后缀的一数。

统计前q条后缀时，零开头分支有ways[len减一][零]条。如果q全部落在零分支就递归它；否则完整零分支的一数可直接查表，余下q减该大小条来自一分支，先给它们各加一个当前一，再递归一分支。前位为一时根本没有一分支。

最后的半个数是同长合法表示中从零开始排名q的那个。首位一先处理，之后仍用零分支大小决定目标落在哪一边，逐位解码，只走rest需要的字符，累计其中的一。

表预处理至八十位，数量、字符块与一的总数均在long long内，而覆盖十的十五次方字符所需长度更小。N为零直接得到零；输入有多组，读至文件结束，不把零当终止符。''',
    'N是连接串字符数；权值从一二三五开始；禁止相邻一；每个表示首位一；块字符数要乘长度；最后可能只读半个表示；排名从零；零询问不终止。',
    r'设所需最大表示长度为D，预处理 $O(D)$；每次询问时间 $O(D)$，空间 $O(D)$。',['数位 DP','组合计数'],D+['counting','recursion','strings','digit-aggregation'])

emit('CF628D','固定长度逐位保留位置奇偶与除m余数',
    '统计等长正整数区间中的d魔法数：从左起偶数位置都等于d，奇数位置都不等于d，并且整个数被m整除；答案模十的九次方加七。',
    r'''两端位数相同，只填同样长度且首位非零的数，位置奇偶由外层循环固定。状态记当前余数和是否贴界；奇数位禁止d，偶数位只允许d，余数按十乘旧值加新位更新。F(x)统计该固定长度下不超过x的合格数，用F(b)减F(a)再加a本身是否合格，避免对2000位字符串做减一。''',
    r'''位置从左往右、从一开始。偶数位必须是d，奇数位必须不是d。若只有一位，就没有偶数位，并不额外要求d出现；例如一位数七可以是零魔法数。

a与b的位数相同，所以区间中的每个数都长L位。不允许通过跳过前导零把短数加入：那既超出区间，也会改变位置奇偶。首位只枚举一至九，再施加奇数位不等于d的限制。

定义F(x)为长度恰为L、不超过x并满足魔法规则、且被m整除的数目。按位置处理，dp[tight][r]保存前缀余数为r的数量。新数码为digit，余数变为十乘r加digit再模m；是否贴界按本位选择更新。

第pos个零起下标为偶数时对应题目的奇数位，禁止digit等于d；下标为奇数时对应偶数位，只允许digit等于d。每轮重建新表，最终只取余数零，贴界与离界两格相加。

通常区间写F(b)减F(a减一)，但这里a可能有两千位。无需引入大整数减法，改写为F(b)减F(a)，再用一次线性扫描判断a本身是否满足位置限制且余数零，满足就加一。

m至多两千，只需滚动保存两行余数表，内存与L无关；时间与L、m、十种候选数码的乘积有关。计数每次模十的九次方加七，差值先加模数防止负数。

前导零规则与d为零不冲突：真实的偶数位置仍然可以且必须放零，奇数位置仍然不允许零；只禁止首位为零。''',
    '位置左起一编号；奇数位禁止d、偶数位固定d；首位非零；等长区间不统计短数；d无需在一位数里出现；F(b)减F(a)要补a；滚动余数表。',
    r'时间 $O(10Lm)$，空间 $O(m+L)$，含输入字符串。',['数位 DP'],D+['strings','modular'])

emit('CF1073E','数码集合压成掩码，每格同时保存数量和数值和',
    '求闭区间内十进制表示至多出现k种不同数码的所有整数之和，答案模998244353。',
    r'''逐位填数，状态记已经出现的十种数码掩码与上界关系，同时保存前缀数量C和数值总和S。接数码d后新总和为十乘S加d乘C，新掩码登记d，种类超过k就拒绝。全零掩码表示尚未开始，前导补零不登记，真实开始后的零要登记。末尾累加总和，两个前缀相减。''',
    r'''数码种类只取决于哪些数字出现过，不取决于各自出现了几次。例如一百零一的实际种类是零和一，共两种。用十位掩码记录这十个布尔条件，位d为一表示已经用过d。

每个前缀状态还需要数量C与数值和S。接上数码d后，每个原值v变成十乘v加d，全部新值的和因此为：

$$S'=10S+dC.$$

只保存数量不能恢复答案；只保存数值和也不知道末位d要重复累加多少次。两张表同步转移，在998244353下取模。

掩码零表示尚未开始。此时继续填零仍保持零，表示较短数字的占位；一旦填非零，掩码便非零，以后追加零就要把数码零的一位登记进去。实际开始以后掩码只增加置一位，不会回到零，所以无需另存started。

预先递推每个掩码的置一数量，超过k的目标直接跳过。tight限制当前最多能填多少，离界后不再受后续上界字符约束。每轮从旧表读、向新表加，不能让本位刚写出的值再次被延长。

一个容易忽略的取模问题是：数量模后等于零，并不代表状态不存在，更不代表它的数值和也为零。代码只在数量和总和都为零时跳过；若数量余数零、总和非零，仍要传播十乘S的贡献。

F(x)统计零至x的合格数值和。全占位零路径最终数值为零，对求和无影响；x非正直接返回零。答案为F(r)减F(l减一)并规范到非负。

k为十时所有正数都允许，可用普通区间整数和作独立检查；k为一时只有各位重复同一非零数码的数，这也说明真实零与前导零不能混淆。''',
    '最多k种而不是恰k种；同一数字重复不新增种类；真实零要登记；前导零不登记；新数值和十乘旧和再加d乘数量；模后计数零不能单独作为跳过依据。',
    r'设十进制位数为D，时间 $O(10D2^{10})$，空间 $O(2^{10}+D)$。',['数位 DP','状压 DP'],D+['strings','bitwise','digit-aggregation','modular'])

# These nine programs actually use capturing lambdas.
from core7_authoring import SPECS
for method in SPECS:
    if method.pid in {'P14074','UVA1640','P2518','P4127','P5128','P14084','SP10606','CF628D','CF1073E'}:
        method.lessons.append('lambda-local')
