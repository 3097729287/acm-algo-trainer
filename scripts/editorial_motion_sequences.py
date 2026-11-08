"""Reviewed array, queue, interval and DP traces from the existing articles."""
from collections import deque
from editorial_motion_assets import Clip,BLUE,GREEN,RED,GRAY,ORANGE

def sequence_clips():
 clips=[]
 c=Clip('window-deques','luogu-training-P1886','同一窗口：先入队，再输出最小值和最大值','队首过期与队尾受支配是两种不同的删除。','位置$i$为当前窗口右端',500)
 a=[1,3,-1,-3,5,3,6,7];low=deque();high=deque();mins=[];maxs=[]
 def window_board(f,i,stage):
  f.row(a,105,'原数组',{j:GREEN if j==i else BLUE if max(0,i-2)<=j<=i else GRAY for j in range(8)},True)
  f.row([f'{j+1}:{a[j]}' for j in low]+['·']*(8-len(low)),215,'最小队列')
  f.row([f'{j+1}:{a[j]}' for j in high]+['·']*(8-len(high)),310,'最大队列')
  f.note(415,'完整窗口最小值：'+(' '.join(map(str,mins)) or '尚未输出'),GREEN)
  f.note(455,'完整窗口最大值：'+(' '.join(map(str,maxs)) or '尚未输出'),BLUE)
 for i,x in enumerate(a):
  expired=[]
  for q in [low,high]:
   while q and q[0]<i-2:expired.append(q.popleft()+1)
  c.frame(f'右端到第 {i+1} 项；先检查队首是否过期，当前 {x} 还没入队。',lambda f:window_board(f,i,'before'),{'phase':'expire','i':i,'low':list(low),'high':list(high),'expired':expired})
  while low and a[low[-1]]>=x:low.pop()
  while high and a[high[-1]]<=x:high.pop()
  low.append(i);high.append(i)
  if i>=2:mins.append(a[low[0]]);maxs.append(a[high[0]])
  c.frame(f'再插入 {x}，从队尾移除不再可能最优的候选。'+('此时才输出当前完整窗口。' if i>=2 else '还没满三项，不输出。'),lambda f:window_board(f,i,'after'),{'phase':'insert','i':i,'low':list(low),'high':list(high),'mins':mins,'maxs':maxs})
 assert mins==[-1,-3,-3,-3,3,3] and maxs==[3,3,5,5,6,7]
 clips.append(c.check('8 3\n1 3 -1 -3 5 3 6 7\n','-1 -3 -3 -3 3 3\n3 3 5 5 6 7\n'))

 c=Clip('previous-window','luogu-training-P1440','当前项要等查询结束后才能入队','本题不含当前项，和 P1886 的时序相反。','查询必须在当前项入队之前完成。')
 a=[7,8,1,4];q=deque();answers=[]
 def previous_board(f,i,phase):
  f.row(a,110,'数值',{j:RED if j==i else GREEN if max(0,i-2)<=j<i else GRAY for j in range(4)},True)
  f.row([f'{j+1}:{a[j]}' for j in q]+['·']*(4-len(q)),225,'队列候选')
  f.row(answers+['·']*(4-len(answers)),330,'已输出')
 for i,x in enumerate(a):
  while q and q[0]<i-2:q.popleft()
  answers.append(a[q[0]] if q else 0)
  c.frame(f'第 {i+1} 项是 {x}，先查之前两项，输出 {answers[-1]}；红格当前项不参与。',lambda f:previous_board(f,i,'query'),{'phase':'query','i':i,'queue':list(q),'answers':answers})
  while q and a[q[-1]]>=x:q.pop()
  q.append(i)
  c.frame(f'查询完才加入 {x}。'+('它会替代较早且更大的 7、8。' if i==2 else '它从下一次查询起才可能被使用。'),lambda f:previous_board(f,i,'insert'),{'phase':'insert','i':i,'queue':list(q)})
 assert answers==[0,7,7,1];clips.append(c.check('4 2\n7 8 1 4\n','0\n7\n7\n1\n'))

 c=Clip('bounded-prefix-queue','luogu-training-P1714','非空蛋糕段：先查旧前缀，再插入当前前缀','队列的合法时间与非空区间条件同时变化。','处理顺序不能交换。',500)
 a=[-2,3,-1,4,-5];prefix=[0]
 for x in a:prefix.append(prefix[-1]+x)
 q=deque([0]);best=-10**9
 def cake_board(f,i,j,phase):
  f.row(a,105,'蛋糕',{k:GREEN if j<=k<i else GRAY for k in range(5)},True)
  f.row(prefix,215,'前缀和',{k:GREEN if k==j else RED if k==i else BLUE for k in range(6)},True,0)
  f.row([f'{k}:{prefix[k]}' for k in q]+['·']*(6-len(q)),325,'候选 j')
  f.note(425,f'长度上限 3；当前最佳非空和 = {best}',GREEN)
 for i in range(1,6):
  while q and q[0]<i-3:q.popleft()
  j=q[0];value=prefix[i]-prefix[j];best=max(best,value)
  assert j<i and i-j<=3
  c.frame(f'右端 {i}：只查 j∈[{max(0,i-3)},{i-1}]，{prefix[i]}−({prefix[j]})={value}。当前前缀还不能作左边界。',lambda f:cake_board(f,i,j,'query'),{'phase':'query','i':i,'j':j,'queue':list(q),'prefix':prefix,'value':value,'best':best})
  removed=[]
  while q and prefix[q[-1]]>=prefix[i]:removed.append(q.pop())
  q.append(i)
  c.frame(f'现在才插入前缀 {i}，移除较大或相等的旧前缀。它只服务后续右端。',lambda f:cake_board(f,i,j,'insert'),{'phase':'insert','i':i,'queue':list(q),'removed':removed})
 assert best==6;clips.append(c.check('5 3\n-2 3 -1 4 -5\n','6\n'))

 c=Clip('next-greater-stack','luogu-training-P5788','弹栈是在确定旧位置的答案','一次新值可能连续解决多个待回答位置；相等不能解决。','弹出$j$后')
 a=[1,4,2,3,5];stack=[];ans=[0]*5
 def stack_board(f,i):
  f.row(a,110,'原数值',{j:GREEN if j==i else BLUE for j in range(5)},True)
  f.row([f'{j+1}:{a[j]}' for j in stack]+['·']*(5-len(stack)),225,'等待栈')
  f.row(ans,330,'答案位置')
 for i,x in enumerate(a):
  while stack and a[stack[-1]]<x:
   j=stack.pop();ans[j]=i+1
   c.frame(f'{x} 严格大于位置 {j+1} 的 {a[j]}：答案是当前位置 {i+1}，随后继续检查新的栈顶。',lambda f:stack_board(f,i),{'phase':'resolve','i':i,'resolved':j,'stack':stack,'answer':ans})
  stack.append(i)
  c.frame(f'把位置 {i+1} 放入等待栈；还没遇到更大值的位置继续保留。',lambda f:stack_board(f,i),{'phase':'push','i':i,'stack':stack,'answer':ans})
 assert ans==[2,5,4,5,0];clips.append(c.check('5\n1 4 2 3 5\n','2 5 4 5 0\n'))

 c=Clip('stable-letter-swaps','luogu-training-P3531','同字母不交叉，C 只越过三个字符','用真实相邻交换对应逆序对的逐次消除。','得到的每个目标位置只使用一次。')
 tokens=['A₁','B','A₂','C'];target={'A₁':2,'B':3,'A₂':4,'C':1}
 for move in range(4):
  inversions=sum(target[tokens[i]]>target[tokens[j]] for i in range(4) for j in range(i+1,4))
  assert inversions==3-move
  def draw(f):
   f.row(['C','A₁','B','A₂'],100,'目标')
   f.row(tokens,220,'当前顺序',{i:GREEN if t=='C' else BLUE for i,t in enumerate(tokens)})
   f.row([target[t] for t in tokens],325,'目标位置')
   f.note(410,f'已交换 {move} 次；剩余逆序 {inversions} 对。A₁ 始终在 A₂ 前。',GREEN)
  c.frame('初始 ABAC，稳定匹配到目标 CABA。' if move==0 else f'C 向左交换一次；累计 {move} 次，没有交换两个 A 的身份。',draw,{'tokens':tokens,'inversions':inversions})
  if move<3:k=tokens.index('C');tokens[k-1],tokens[k]=tokens[k],tokens[k-1]
 clips.append(c.check('4\nABAC\nCABA\n','3\n'))

 c=Clip('cancel-appointments','luogu-training-P2161','取消旧预约，不把旧区间并入新预约','删除整条旧预约与区间并集很容易混淆。','闭区间共享端点也相交',470)
 states=[([(1,10),(20,30)],(9,21),'新预约尚未加入；它分别与两条旧预约相交。'), ([(9,21)],None,'两条旧预约同时取消，实际只插入原来的 [9,21]。'), ([(9,21)],(29,29),'再请求 [29,29]，它在 21 右侧，不相交。'), ([(9,21),(29,29)],None,'没有取消任何旧预约，现在共有两条。')]
 for intervals,pending,caption in states:
  def draw(f):
   for tick in [1,9,10,20,21,29,30]:
    x=135+(tick-1)*21;f.line(x,90,x,100,GRAY);f.text(x,80,tick,GRAY,size=16,anchor='middle')
   f.line(135,100,744,100,GRAY)
   for i,(l,r) in enumerate(intervals):
    y=155+i*75;color=RED if pending and not(r<pending[0] or pending[1]<l) else BLUE
    if l==r:f.circle(135+(l-1)*21,y,'',color,radius=7)
    else:f.line(135+(l-1)*21,y,135+(r-1)*21,y,color,width=12)
    f.text(35,y+7,f'[{l},{r}]',color,size=19)
   if pending:
    l,r=pending
    if l==r:f.circle(135+(l-1)*21,330,'',GREEN,radius=7)
    else:f.line(135+(l-1)*21,330,135+(r-1)*21,330,GREEN,width=12)
    f.text(35,337,'新请求',GREEN,size=19)
   f.note(420,'新预约的端点保持原值，旧预约的剩余部分也不会留下。')
  c.frame(caption,draw,{'kept':intervals,'pending':pending})
 clips.append(c.check('6\nA 1 10\nA 20 30\nA 9 21\nB\nA 29 29\nB\n','0\n0\n2\n1\n0\n2\n'))

 c=Clip('difference-event-time','luogu-training-P4939','坐标可以预读，更新仍须按时序生效','未来事件不能影响早先查询，闭右端之后才撤销。','重放命令仍必须保持输入顺序。')
 coordinates=[2,5,6,11];events=[0]*4
 actions=[('update',2,5),('query',5,None),('update',5,10),('query',5,None),('query',6,None)]
 for action,x,y in actions:
  result=None
  if action=='update':events[coordinates.index(x)]+=1;events[coordinates.index(y+1)]-=1
  else:result=sum(v for p,v in zip(coordinates,events) if p<=x)
  def draw(f):
   f.row(coordinates,110,'事件坐标',{i:GREEN if action=='query' and p<=x else BLUE for i,p in enumerate(coordinates)})
   f.row([f'{v:+d}' for v in events],225,'已生效值')
   f.note(335,f'当前查询 {x}：只累加不大于它的坐标，答案 {result}。' if action=='query' else f'本轮增加 [{x},{y}]：在 {x} 加一，在 {y+1} 撤销。',GREEN)
   f.note(405,'5 虽已预读，第二次增加发生前仍是零。' if events[1]==0 else '第二次增加后 5 处才变成 +1；6 处撤销第一段。')
  c.frame(f'查询 {x} 得到 {result}。' if action=='query' else f'执行增加 [{x},{y}]，只让这一条命令生效。',draw,{'action':action,'x':x,'events':events,'result':result})
 clips.append(c.check('10 5\n0 2 5\n1 5\n0 5 10\n1 5\n1 6\n','1\n2\n1\n'))

 c=Clip('color-window','luogu-training-P2564','同色数量归零，窗口才失去一种颜色','同坐标的不同颜色与移除最后一颗的时刻需要同步看。','一旦covered等于K',470)
 beads=[(1,'红'),(1,'蓝'),(5,'红'),(6,'绿'),(8,'蓝')];palette={'红':RED,'蓝':BLUE,'绿':GREEN};left=0;counts={k:0 for k in palette};best=10**9
 def color_board(f,right):
  f.row([str(p)+color for p,color in beads],110,'有序珠子',{i:palette[color] if left<=i<=right else GRAY for i,(p,color) in enumerate(beads)},True)
  f.row([counts[k] for k in palette],225,'红 蓝 绿',{i:palette[k] if counts[k] else GRAY for i,k in enumerate(palette)})
  covered=sum(v>0 for v in counts.values());f.note(335,f'窗口含 {covered}/3 色；'+(f'最短坐标差 {best}' if best<10**9 else '还没有完整答案'),GREEN)
  f.note(405,'同坐标两颗珠子仍是两个位置；长度用坐标差，不加一。')
 for right,(pos,color) in enumerate(beads):
  counts[color]+=1
  c.frame(f'右端加入坐标 {pos} 的{color}珠；该色计数增加一。',lambda f:color_board(f,right),{'phase':'extend','left':left,'right':right,'counts':counts})
  while all(counts.values()):
   best=min(best,beads[right][0]-beads[left][0]);removed=beads[left];counts[removed[1]]-=1;left+=1
   c.frame(f'先记录长度，再移除坐标 {removed[0]} 的{removed[1]}珠；'+('这一色已经归零，停止收缩。' if counts[removed[1]]==0 else '仍有同色珠子，可以继续收缩。'),lambda f:color_board(f,right),{'phase':'shrink','left':left,'right':right,'counts':counts,'best':best})
 assert best==3;clips.append(c.check('5 3\n2 1 5\n2 1 8\n1 6\n','3\n'))

 c=Clip('playlist-wrap','luogu-training-CF1237D','同一首 2，在遇到 5 前后命运不同','比较的是当前历史最大值，并且触发曲目不计。','历史最大值只来自已经听过的曲目',470)
 a=[3,3,2,5];played=[];history=0
 for i,x in enumerate((a*2)[:7]):
  old_history=history;bad=bool(played) and 2*x<history
  if not bad:played.append(x);history=max(history,x)
  def draw(f):
   f.row((a*2)[:7],110,'实际播放',{k:RED if k==i and bad else GREEN if k<i or k==i and not bad else GRAY for k in range(7)},True)
   f.line(145+4*(840-175)/7-2,85,145+4*(840-175)/7-2,180,ORANGE,dash=True)
   f.note(220,'虚线后是第二圈；它们是新的播放次数，不是重复位置去重。',ORANGE)
   f.row([old_history if i else '空',history,len(played)],290,'旧/新/次数')
   f.note(395,(f'新歌 {x}：2×{x} '+('<' if bad else '≥')+f' 旧最大值 {old_history}；'+('在听它之前停止。' if bad else '可以听完。')) if i else '第一首没有已听历史，必定可以听。',RED if bad else GREEN)
  c.frame(f'读到 {x}，'+('它小于历史最大值 5 的一半，停在这里，已听六首。' if bad else '可以听完并更新历史。'),draw,{'i':i,'x':x,'oldHistory':old_history,'history':history,'heard':len(played),'bad':bad})
 assert len(played)==6;clips.append(c.check('4\n3 3 2 5\n','6 5 4 3\n'))

 c=Clip('bounded-flower-layers','luogu-training-P1077','新花种只从上一种花的整行读取','原地累加会突破当前花种的数量上限。','每轮只读上一轮')
 old=[1,1,1,1,0];new=[0]*5
 for amount in range(4):new[amount]=sum(old[amount-count] for count in range(min(2,amount)+1))
 for count in range(3):
  source=4-count;new[4]+=old[source]
  def draw(f):
   f.row(old,110,'旧：只用 A',{source:GREEN},True,0)
   f.row(new,245,'新：加入 B',{4:GREEN},True,0)
   f.note(350,f'B 最多 2 盆。本次放 {count} 盆：读取旧行 {source} 盆的方案数 {old[source]}。',GREEN)
   f.note(415,'新行已经算出的数，不能当作另一种旧方案再次读入。')
  c.frame(f'计算总数四盆，令 B={count}；从旧行 A={source} 的方案累加，新答案变为 {new[4]}。',draw,{'old':old,'new':new,'countB':count,'source':source})
 assert new==[1,2,3,3,2];clips.append(c.check('2 4\n3 2\n','2\n'))

 c=Clip('triangle-bonus-layers','luogu-training-P1544','必须先经过负分根，三倍次数另外记','路径位置与已用次数两项状态不能合并，也不能用零代替不可达。','同一位置、同一已用次数',480)
 states=[([-2,-6],None,'根 −2：不用三倍得 −2，用一次得 −6，两种状态都要保留。'),([-2,-6],[[-5,-9],[2,10]],'计算下一行时只读根的旧状态，负分根不能跳过。'),([-2,-6],[[-5,-9],[2,10]],'右下用一次三倍：−2+3×4=10；左下不用为 −5。'),([-2,-6],[[-5,-9],[2,10]],'允许不超过一次；在所有末点、所有次数中取最大，答案 10。')]
 for step,(old,new,caption) in enumerate(states):
  def draw(f):
   f.circle(420,110,'−2',BLUE,28);f.line(400,133,260,205);f.line(440,133,580,205)
   f.circle(240,225,'−3',BLUE,28);f.circle(600,225,'4',GREEN if step>=2 else BLUE,28)
   f.text(420,165,'用 0 次：−2；用 1 次：−6',BLUE,size=19,anchor='middle')
   if new:
    f.text(240,300,'0 次：−5 / 1 次：−9',BLUE,size=19,anchor='middle');f.text(600,300,'0 次：2 / 1 次：10',GREEN,size=19,anchor='middle')
   f.note(410,'每条路径都必须含根。三倍可以不用，不能凭空以零分开始。')
  c.frame(caption,draw,{'root':old,'last':new})
 clips.append(c.check('2 1\n-2\n-3 4\n','10\n'))

 c=Clip('fountain-successors','luogu-training-P7167','满盘之后，水只流向首个更大直径','跳过的圆盘不扣容量；等于整段容量时不能跳过。','询问从起点',570)
 diameter=[2,5,4,3,6];capacity=[2,3,9,9,4]
 stages=[([0,0,0,0,0],6,'从 1 号倒入 6；实际后继链是 1→2→5。'),([2,0,0,0,0],4,'1 号装下 2，剩下 4 流向更大直径的 2 号。'),([2,3,0,0,0],1,'2 号再装 3；3、4 号直径都较小，被完全跳过。'),([2,3,0,0,1],0,'剩下 1 在 5 号停留，答案 5。'),([0,0,0,0,0],5,'另一份独立询问重新从空盘开始，倒入 5。'),([2,3,0,0,0],0,'1、2 号恰好装满 5，水停在 2 号；不能跳到 5 号。')]
 for amounts,remaining,caption in stages:
  def draw(f):
   for i,(d,cap,amount) in enumerate(zip(diameter,capacity,amounts)):
    y=100+i*68;f.text(40,y+7,f'{i+1} 号',size=20);f.line(300-d*23,y,300+d*23,y,GREEN if amount else BLUE,width=8)
    f.text(490,y+7,f'直径 {d}；本次 {amount}/{cap}',GREEN if amount else GRAY,size=20)
   f.note(485,'跳两盘的容量和是 2+3=5，只在 5 < 剩余水量 时接受。',GREEN)
   f.note(535,'3、4 号始终未接到水；每次询问的水量独立。')
  c.frame(caption,draw,{'amounts':amounts,'remaining':remaining})
 clips.append(c.check('5 2\n2 2\n5 3\n4 9\n3 9\n6 4\n1 6\n1 5\n','5\n2\n'))
 return clips
