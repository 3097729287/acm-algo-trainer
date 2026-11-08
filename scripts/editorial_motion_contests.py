"""Concrete traces of the difficult transitions already explained in old contests."""
from editorial_motion_assets import Clip,BLUE,GREEN,RED,GRAY,ORANGE

def contest_clips():
 clips=[]
 c=Clip('odd-cycle-reconstruction','ABC 472::E','同层冲突边，接上两条父链得到奇环','两条链都要反转/拼接，而共同祖先只能出现一次。','代码先 BFS 保存',610)
 points={1:(420,100),2:(240,220),3:(600,220),4:(180,350),5:(660,350)};edges=[(1,2),(1,3),(2,4),(3,5),(4,5)]
 stages=[([4],[5],'BFS 中 4、5 同为偶数深度；它们之间的边产生冲突。'),([4,2],[5,3],'两端同时上提，各自保存向上的父链。'),([4,2,1],[5,3],'在 1 首次相遇；只给左链补一次公共祖先。'),([4,2,1],[3,5],'把右链反转，才能从公共祖先继续向下走。'),([4,2,1,3,5],[],'得到 4→2→1→3→5，最后由原边 5→4 闭合，五点奇环。')]
 for pu,pv,caption in stages:
  def draw(f):
   f.graph(points,edges,special={(4,5):RED})
   for node,(x,y) in points.items():f.circle(x,y,node,GREEN if node in [1,4,5] else BLUE,radius=22)
   f.row(pu+['·']*(5-len(pu)),435,'左链/结果')
   f.row(pv+['·']*(5-len(pv)),530,'右链')
  c.frame(caption,draw,{'left':pu,'right':pv,'sameDepthConflict':[4,5]})
 clips.append(c.check('1\n5 5\n1 2\n1 3\n2 4\n3 5\n4 5\n','5\n4 2 1 3 5\n'))

 c=Clip('mex-threshold-assign','ABC 470::G','示例 [2,1,0,2,1,4]：分段压低合法左端数','首个超限位置不一定是区间左边界，且整层完成后才能计贡献。','仍取官方数组',520)
 a=[2,1,0,2,1,4];g=[7]*6;total=0
 def mex_board(f,value,last,first,right,left):
  f.row(a,105,'原数组',indices=True)
  f.row(last,215,f'last {value}',{i:GREEN if first is not None and i==first else BLUE for i in range(6)})
  f.row(g,325,'正在更新 G',{i:GREEN if first is not None and first<=i<=right else BLUE for i in range(6)})
  f.note(435,f'已完整处理层的贡献和：{total}。尚未完成的层不提前求和。',GREEN)
  f.note(480,f'当前仅处理右端范围 [{left+1},{right+1}]；这段以外的格子不改。',size=19)
 for value in range(3):
  last=[];previous=0
  for i,x in enumerate(a,1):
   if x==value:previous=i
   last.append(previous)
  left=0
  while left<6:
   right=left
   while right+1<6 and last[right+1]==last[left]:right+=1
   cap=last[left];first=next((i for i in range(left,right+1) if g[i]>cap),None)
   for i in range(left,right+1):g[i]=min(g[i],cap)
   assert g==sorted(g)
   done=right==5
   if done:total+=sum(g)
   description=f'加入值 {value}，右端段 [{left+1},{right+1}] 的上限为 {cap}；'+(f'从 {first+1} 开始的超限后缀被赋值。' if first is not None else '没有超限位置，整段不改。')
   if done:description+=f' 本层和为 {sum(g)}。'
   c.frame(description,lambda f:mex_board(f,value,last,first,right,left),{'value':value,'last':last,'range':[left,right],'cap':cap,'first':first,'g':g,'layerComplete':done,'total':total})
   left=right+1
 brute=0
 for i in range(6):
  for j in range(i,6):
   found=set(a[i:j+1]);mex=0
   while mex in found:mex+=1
   brute+=mex
 assert total==brute==31;clips.append(c.check('6\n2 1 0 2 1 4\n','31\n'))

 c=Clip('dice-old-new-rows','Div.3 1080::C','同一位置的六种新末面，始终只读旧行','覆盖旧行会让同一枚骰子被重复接到序列里。','但旧、新两层必须分开读写',500)
 a=[1,6,1];old=[0,1,1,1,1,1];new=[None]*6
 def dice_board(f,target=None):
  f.row(a,100,'原序列')
  allowed=[u for u in range(1,7) if target and u!=target and u+target!=7]
  f.row(old,220,'旧末面',{u-1:GREEN for u in allowed},True)
  f.row(['·' if v is None else v for v in new],335,'新末面',{target-1:GREEN} if target else {},True)
  f.note(450,'当前原值：'+str(current)+'；绿格是允许读取的旧末面，不读已写的新格。',GREEN)
 current=6
 c.frame('处理完第一位 1，旧行是 0、1、1、1、1、1。准备处理第二位 6。',dice_board,{'old':old,'new':new,'position':2})
 for v in range(1,7):
  allowed=[u for u in range(1,7) if u!=v and u+v!=7];new[v-1]=min(old[u-1] for u in allowed)+(v!=current)
  if v<=2:c.frame(f'新末面取 {v}：允许旧面 {"、".join(map(str,allowed))}，新代价是 {new[v-1]}。'+('仍要读取旧面 1 的零，不能读取刚写的新代价二。' if v==2 else ''),lambda f:dice_board(f,v),{'old':old,'new':new,'v':v,'allowed':allowed})
 c.frame('整行六格都完成后，才交换新旧角色。',dice_board,{'old':old,'new':new})
 old=new[:];current=1;new=[None]*6
 for v in range(1,7):new[v-1]=min(old[u-1] for u in range(1,7) if u!=v and u+v!=7)+(v!=current)
 c.frame('最后一位仍取 1，可从旧末面 2 接来，完整方案 1→2→1 只修改中间一次。',lambda f:dice_board(f,1),{'old':old,'new':new,'answer':min(new),'witness':[1,2,1]})
 assert new==[1,2,2,2,2,2];clips.append(c.check('1\n3\n1 6 1\n','1\n'))

 c=Clip('signed-weight-layers','lanqiao:2021:省:::P8742','每枚砝码只从旧集合产生三种去向','正负两边都可用；同一枚砝码不能反复参与新状态。','以样例 N=3',560)
 old={0}
 for weight in [1,4,6]:
  new={s+d for s in old for d in [-weight,0,weight]}
  def draw(f):
   f.row(sorted(old),100,'旧带符号和')
   values=sorted(new)
   for i in range(0,len(values),7):f.row(values[i:i+7],215+(i//7)*80,'新可达' if i==0 else '',{j:GREEN for j in range(len(values[i:i+7]))})
   f.note(510,f'当前砝码 {weight}：每个旧 s 只产生 s−{weight}、s、s+{weight}。',GREEN)
  c.frame(f'加入重量 {weight}，只从完整的旧集合生成新集合；本轮新数不会再使用这枚砝码。',draw,{'weight':weight,'old':sorted(old),'new':sorted(new)})
  old=new
 positives=sorted(x for x in old if x>0);assert positives==[1,2,3,4,5,6,7,9,10,11]
 c.frame('最后只数正数，零和左右镜像不重复计数；正重量共十种，八不可达。',lambda f:(f.row(positives,150,'可称正数',{i:GREEN for i in range(len(positives))}),f.note(300,'{1,2,3,4,5,6,7,9,10,11}，共 10 种；0 不计。',GREEN)),{'positive':positives,'answer':10})
 clips.append(c.check('3\n1 4 6\n','10\n'))

 c=Clip('subsequence-descending','lanqiao:2019:国:::P8703','倒序更新，保证当前 B 只被选择一次','需要同时看同一数组格子的新旧版本。','倒序保证 dp[j-1]',500)
 old=[0,0,1,99];dp=old[:];updated=set()
 def subseq_board(f,source=None,destination=None):
  f.note(100,'补充例子：S=AAB，T=ABB；已经处理前缀 AA，正读最后的 B。')
  f.row(['∞' if x==99 else x for x in old],190,'旧行快照',{source:GREEN} if source is not None else {},True,0)
  f.row(['∞' if x==99 else x for x in dp],320,'实际 dp',{j:GREEN if j in updated else GRAY for j in range(4)},True,0)
  if destination is not None:
   width=(840-175)/4;f.line(145+(source+.5)*width,238,145+(destination+.5)*width,312,GREEN,width=3)
  f.note(455,'灰格尚属旧版本，绿格已经更新；读取的左邻仍未写过。',GREEN)
 c.frame('初始快照为 0、0、1、∞。从 j=3 向左更新，不能从 j=1 向右覆盖。',subseq_board,{'old':old,'dp':dp,'updated':[]})
 for j in [3,2,1]:
  assert j-1 not in updated
  cost=('B'!='ABB'[j-1]);dp[j]=min(dp[j],dp[j-1]+cost);updated.add(j)
  c.frame(f'更新 j={j}，读取尚未覆盖的 dp[{j-1}]={old[j-1]}，写入 {dp[j]}。',lambda f:subseq_board(f,j-1,j),{'old':old,'dp':dp,'j':j,'source':j-1,'updated':sorted(updated)})
 assert dp==[0,0,0,1];clips.append(c.check('AAB\nABB\n','1\n'))

 c=Clip('bracket-prefix-affine','lanqiao:2021:国:::P8765','括号翻转：段内镜像，后缀统一平移','后缀平移量必须用修改前的两个端点，不能读回新值。','翻转 1 3 5',560)
 before=[0,1,2,3,2,1,2,1];after=[0,1,2,1,2,3,4,3]
 for phase in range(5):
  values=before if phase<3 else after
  def draw(f):
   f.line(75,400,780,400,GRAY);f.line(75,400,75,100,GRAY)
   f.line(75,270,780,270,ORANGE,dash=True);f.text(30,265,'2',ORANGE,size=18)
   for i in range(8):
    x=100+i*90;y=400-values[i]*65;color=GREEN if 3<=i<=5 else ORANGE if i>5 else BLUE
    if phase>=3:
     oldy=400-before[i]*65;f.circle(x,oldy,'',GRAY,radius=4)
    if i:
     f.line(100+(i-1)*90,400-values[i-1]*65,x,y,color,width=4)
    f.circle(x,y,'',color,radius=6);f.text(x,y-17,values[i],color,size=18,anchor='middle');f.text(x,430,i,GRAY,size=17,anchor='middle')
   f.note(490,'旧 P[2]=2、旧 P[5]=1；段内 4−P，后缀加 −2×(1−2)=2。',GREEN,size=19)
   if phase==4:f.note(535,'翻转后问 L=3：P[3]=1 已低于基线 2，答案 0。',RED)
  caption=['样例原前缀曲线，准备翻转位置三到五。','先保存修改前 P[2]=2、P[5]=1。之后不能用已修改的端点代替。','段内关于基线二镜像，后缀统一加二；两段公式属于同一次操作。','按旧端点一次得到整条新曲线，前面不变，段内镜像，后缀上移。','新曲线在第三位就低于查询基线，因此无法从第三位形成合法括号段。'][phase]
  c.frame(caption,draw,{'phase':phase,'prefix':values,'oldLeft':2,'oldRight':1,'suffixShift':2})
 clips.append(c.check('7 4\n((())()\n2 3\n2 2\n1 3 5\n2 3\n','4\n7\n0\n'))

 c=Clip('group-add-compensation','lanqiao:2020:省:1::P8710','新加入的结点，不能继承连通块过去的加分','根标记变化和挂接差值要同时维护，合并本身不能改变旧答案。','以样例 `4 8`',520)
 parent=list(range(5));size=[1]*5;delta=[0]*5;tag=[0]*5;actions=[(1,1,2),(2,1,10),(2,3,5),(1,4,1),(2,2,2),(1,1,2),(1,2,4),(2,2,1)]
 def find(x):
  if parent[x]!=x:
   old=parent[x];parent[x]=find(old);delta[x]+=delta[old]
  return parent[x]
 for op,a,b in actions:
  if op==1:
   x,y=find(a),find(b)
   if x!=y:
    if size[x]<size[y]:x,y=y,x
    parent[y]=x;delta[y]=tag[y]-tag[x];size[x]+=size[y]
  else:tag[find(a)]+=b
  roots=[find(i) for i in range(1,5)];values=[delta[i]+tag[roots[i-1]] for i in range(1,5)]
  def draw(f):
   f.row(parent[1:],105,'父亲',indices=True);f.row(delta[1:],215,'边差 d',indices=True);f.row(values,330,'实际信息',indices=True)
   f.note(445,f'根 1 的 tag={tag[1]}；根 3 的 tag={tag[3]}。实际值 = 路径差 + 根标记。',GREEN)
   if parent[4]==1:f.note(490,'结点 4 的补偿始终是 −10，所以它没有继承加入前的十。',RED,size=19)
  caption=f'连接 {a}、{b}：合并本身不改变任何结点已有信息。' if op==1 else f'给 {a} 所在块增加 {b}，只改该块根标记，块内实际值一起增加。'
  if (op,a,b)==(1,4,1):caption+=' 4 挂到 1，差值必须为 0−10=−10。'
  c.frame(caption,draw,{'parent':parent,'delta':delta,'tag':tag,'values':values,'operation':[op,a,b]})
 assert values==[13,13,5,3];clips.append(c.check('4 8\n1 1 2\n2 1 10\n2 3 5\n1 4 1\n2 2 2\n1 1 2\n1 2 4\n2 2 1\n','13 13 5 3\n'))

 c=Clip('successor-wrap-and-compress','remote:nowcoder:142559::D','先走原环步数，再跳过占用格','线性哨兵触发环绕；压缩路径不等于重编号。','原题包含两种不同的移动',560)
 parent=list(range(8));occupied=set();pos=1;answer=0
 def find(x):
  if parent[x]!=x:parent[x]=find(parent[x])
  return parent[x]
 def locker_board(f,focus=None):
  f.row(['占用' if i in occupied else '空' for i in range(1,7)],110,'原环格子',{i-1:GRAY if i in occupied else GREEN for i in range(1,7)},True)
  f.row([10,20,30,40,50,60],215,'本图标签')
  f.row(parent[1:],325,'链接目标',{i-1:GREEN for i in (focus or [])},True)
  f.note(430,'编号七只是线性哨兵，没有标签，也不是额外储物格。',ORANGE)
  f.note(510,f'当前停留 {pos}；已取标签和 {answer}。原环始终是六格。',GREEN)
 for distance in [6,1,4]:
  start=1+(pos-1+distance)%6;pos=find(start);occupied.add(pos);answer+=pos*10;parent[pos]=find(pos+1)
  c.frame(f'沿原六格走 {distance} 步，落到 {start} 并占用；占用后让它指向后继空格。',locker_board,{'parent':parent,'occupied':sorted(occupied),'pos':pos,'answer':answer})
 c.frame('第四轮再走六步，仍落在已占用的六；先查 6→7，发现到达哨兵。',lambda f:locker_board(f,[6,7]),{'parent':parent,'occupied':sorted(occupied),'start':6,'path':[6,7]})
 c.frame('从一号重新找：1→2→3。这里是在找空格，不是在重新计算步数。',lambda f:locker_board(f,[1,2,3]),{'parent':parent,'occupied':sorted(occupied),'path':[1,2,3]})
 pos=find(1)
 c.frame('路径压缩后 1、2 直接指向空格 3；编号与原来的步数都没变。',lambda f:locker_board(f,[1,2,3]),{'parent':parent,'occupied':sorted(occupied),'pos':pos})
 occupied.add(pos);answer+=pos*10;parent[pos]=find(pos+1)
 c.frame('占用三后，3 又指向 4；旧的 1→3 链仍可继续追到下一空格。',locker_board,{'parent':parent,'occupied':sorted(occupied),'pos':pos,'answer':answer})
 assert answer==120 and pos==3;clips.append(c.check('6 4\n10 20 30 40 50 60\n6 1 4 6\n','120 3\n'))

 c=Clip('invader-history-query','ARC 231::A','三事件例子：先查询历史，再插入本轮剑状态','历史位置和记账值同时影响下一次选择；不能只保留上一次事件。','官方第一例的事件',540)
 events=[(0,4,28),(2,9,11),(4,5,26)];history=[(0,0,0,0)];prefix=0;best=0
 for index,(x,y,z) in enumerate(events,1):
  candidates=[(g+(x-a)**2+(y-b)**2,j) for a,b,g,j in history];value,previous=min(candidates);g=value-z;prefix+=z;best=min(best,g)
  def draw(f):
   points={0:(115,325),1:(115,225),2:(375,85),3:(635,205)};edges=[(previous,index,'平方距离 '+str((x-events[previous-1][0])**2+(y-events[previous-1][1])**2) if previous else '平方距离 '+str(x*x+y*y))]
   f.graph(points,edges,active=[index,previous],directed=True)
   for node,(px,py) in points.items():
    coords=[(0,0),(0,4),(2,9),(4,5)][node];f.text(px-36 if node in [0,1] else px+31,py+7,f'({coords[0]},{coords[1]})',GRAY,size=18,anchor='end' if node in [0,1] else 'start')
   f.row([item[2] for item in history]+[g],405,'g 历史/新',{len(history):GREEN},True,0)
   f.note(505,f'本轮 g={g}；真实本轮剑费用 P+g={prefix}+({g})={prefix+g}。',GREEN,size=19)
  c.frame(f'事件 {index} 先查询旧历史，最优前驱是 {previous}，算出 g={g}；之后才允许插入这个新状态。',draw,{'index':index,'history':[list(v) for v in history],'newG':g,'previous':previous,'prefix':prefix,'realSwordCost':prefix+g})
  history.append((x,y,g,index))
 assert prefix+best==44;clips.append(c.check('1\n3\n0 4 28\n2 9 11\n4 5 26\n','44\n'))

 c=Clip('grid-delete-closure','ABC 472::G','删掉上方负段，也会被迫删掉下方正段','动态障碍的传播与闭合删除集需要在实际格子上对照。','取两行五列的网格',550)
 grid=['---#+','++###'];points={'S':(485,110),'U':(485,235),'V':(610,365),'P':(755,235),'T':(755,445)};edges=[('S','U','3'),('U','V','∞'),('V','T','2'),('P','T','1')]
 for phase in range(5):
  deleted=phase>=3
  def draw(f):
   for r,row in enumerate(grid):
    for col,char in enumerate(row):
     removed=deleted and (r==0 and col<3 or r==1 and col<2)
     color=GRAY if char=='#' or removed else GREEN if (r,col)==(0,4) else ORANGE if phase==2 and r==1 else BLUE
     f.box(28+col*64,135+r*72,59,59,'#' if removed else char,color,'#f2f4f7' if char=='#' or removed else '#fff',size=25)
   f.note(330,'U：−3；V：+2；P：+1',size=19,x=28)
   f.graph(points,edges,active=['S','U','V'] if phase>=2 else ['U'] if phase else [],special={('V','T'):RED} if deleted else {},directed=True)
   f.note(510,('删除完成：' if deleted else '若删除完成：')+'权值和 −1，原总分 0，保留分数 1。',GREEN,size=19)
  caption=['原网格总分零；U 在上、V 在下，右上正号 P 可以独立保留。','选择 U：左右传播会覆盖整个连续负段，不能只删其中一格。','U 向下触及 V，V 也必须删除；橙色是传播到的待删区域。','整次操作完成，U、V 都变障碍，右上 P 留下，得到一分。','网络里同时选择 U、V，仅切 V→T 的容量二；不是只删 U 的非法选择。'][phase]
  c.frame(caption,draw,{'phase':phase,'deletedSegments':['U','V'] if deleted else [],'score':1 if deleted else 0,'cutCapacity':2 if deleted else None})
 clips.append(c.check('2 5\n---#+\n++###\n','1\n'))
 return clips
