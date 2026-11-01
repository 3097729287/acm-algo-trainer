"""Geometry and concrete state objects for the path/enumeration unit."""
import base64
import hashlib
import json
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries
from core7_figures_topology import arrow


def attach_figures(specs):
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf8'))}
    def save(pid,f,caption):
        path=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode();key='assets/core7/'+pid+'.svg'
        old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)

    f=Figure('每次选能落脚的最右位置：一到四，再到八',315)
    values=list('10010101');f.row(values,155,x=45,width=84,colors={i:GREEN if v=='1' else GRAY for i,v in enumerate(values)})
    for i in range(8):f.text(85+i*84,235,i+1,GRAY,anchor='middle')
    arrow(f,85,130,337,130,GREEN);arrow(f,337,100,673,100,GREEN)
    f.text(170,112,'跳 3 格',GREEN,size=20);f.text(455,82,'跳 4 格',GREEN,size=20)
    f.text(45,287,'最大步长为 4；起点不计跳数，共两跳',size=21)
    save('CF910A',f,'绿色格是荷叶。跳四格的范围内选最右荷叶，不把没有荷叶的位置当落点。')

    f=Figure('修路付的是损坏部分，完好长路仍为零',365)
    p={1:(90,185),2:(355,100),3:(355,280),4:(665,185)}
    for u,v,cost,color in [(1,2,0,GRAY),(2,4,100,RED),(1,3,0,GREEN),(3,4,4,GREEN)]:
        f.line(*p[u],*p[v],color,width=4)
    for u,(x,y) in p.items():f.circle(x,y,'A' if u==1 else 'B' if u==4 else u)
    f.text(170,115,'完好：0',GRAY,size=20);f.text(470,105,'损坏：100',RED,size=20)
    f.text(160,290,'完好：0',GREEN,size=20);f.text(485,285,'损坏：4',GREEN,size=20)
    f.text(70,350,'选择 A→3→B，修复费 0+4=4',GREEN,size=22)
    save('P3905',f,'图上标注重新赋予的修复费用；原路长一百的 A 到二号仍完好，不需要支付一百。')

    f=Figure('圆内免费，只累加圆外的三段间隙',355)
    f.circle(230,165,'',GREEN,radius=80);f.circle(470,165,'',GREEN,radius=40)
    for a,b,c in [(70,150,RED),(150,310,GREEN),(310,430,RED),(430,510,GREEN),(510,590,RED)]:f.line(a,165,b,165,c,width=6)
    f.circle(70,165,'',BLUE,radius=5);f.circle(590,165,'',BLUE,radius=5)
    f.text(70,205,'起点 −4',BLUE,size=18,anchor='middle');f.text(230,270,'圆心 0，半径 2',GREEN,size=18,anchor='middle')
    f.text(470,235,'圆心 6，半径 1',GREEN,size=18,anchor='middle');f.text(625,205,'终点 9',BLUE,size=18,anchor='middle')
    for x,label in [(110,2),(370,3),(550,2)]:f.text(x,145,label,RED,anchor='middle')
    f.text(70,325,'红色暴露长度：2+3+2=7；绿色段不计费',size=21)
    save('AT_arc064_c',f,'圆心和半径按同一尺度绘制；利用两个屏障，最小辐射长度为七，不能把圆内路长也计入。')

    f=Figure('去重后有两条点序列，不是三条道路记录',385)
    p={1:(80,190),2:(315,95),3:(315,280),4:(650,190)}
    for u,v in [(1,2),(1,3),(2,4),(3,4)]:
        x,y=p[u];X,Y=p[v];arrow(f,x+25,y,X-25,Y,BLUE);f.text((x+X)/2,(y+Y)/2-10,1,BLUE,size=20)
    for u,(x,y) in p.items():f.circle(x,y,u)
    f.text(50,335,'输入中 1→2、权 1 出现两次，图上只保留一份',RED,size=20)
    f.text(80,372,'最短长度 2；序列为 1→2→4 和 1→3→4',GREEN,size=21)
    save('P1608',f,'两条不同点序列各计一次；重复输入的同一对端点、同一权值不能让第一种序列计两次。')

    f=Figure('包装三、六、十：同余类从最小值起连续可达',355)
    for row,(residue,values,first) in enumerate([(0,[0,3,6,9,12,15,18],0),(1,[1,4,7,10,13,16,19],10),(2,[2,5,8,11,14,17,20],20)]):
        y=80+row*75;f.text(25,y+32,'余 '+str(residue),size=20)
        f.row(values,y,x=120,width=87,colors={i:GREEN if v>=first else RED for i,v in enumerate(values)})
    f.text(45,335,'绿色可组成；红色不可组成；最后一个红数是 17',size=21)
    save('P2737',f,'每行相差三。余数二最小可达值是二十，所以前一个同余数十七是该类最后的缺口。')

    f=Figure('每片灌木都要比较去程与回程的和',390)
    from core7_cases_shortest import knight_map,platform_walk,fare_time
    land=list('4000'+'0000'+'0230'+'0004');assert knight_map(land,4,4)==5
    for r in range(4):
        for c in range(4):
            char=land[r*4+c];label={'2':'起点','3':'骑士','4':'灌木'}.get(char,'')
            color=RED if char=='3' else GREEN if char=='4' else BLUE
            f.box(40+65*c,65+65*r,60,60,label,color,size=16)
    f.text(345,110,'左上灌木：3+4=7',size=21);f.text(345,175,'右下灌木：3+2=5',GREEN,size=21)
    f.text(345,240,'取得前不能经过红格',RED,size=20)
    f.text(40,367,'可先向下，再沿最下行取灌木，最后回到骑士',size=20)
    save('P5195',f,'这张实际四邻地图的最短任务长度为五；两次 BFS 分别限制取灌木前后的可走格。')

    f=Figure('集合内两端费用之和，拆成经过中转点的两步',390)
    p={1:(80,180),2:(265,95),3:(265,280)}
    for u,v,label in [(1,2,7),(1,3,3),(2,3,6)]:
        f.line(*p[u],*p[v],BLUE);f.text((p[u][0]+p[v][0])/2+8,(p[u][1]+p[v][1])/2-8,label,BLUE,size=19)
    for u,(x,y) in p.items():f.circle(x,y,u)
    center=(535,190);members=[(430,95,1,2),(680,95,2,5),(680,285,3,1)]
    for x,y,u,w in members:
        f.line(*center,x,y,GREEN);f.circle(x,y,u);f.text((x+center[0])/2,(y+center[1])/2-9,w,GREEN,size=19)
    f.circle(*center,'S',GREEN)
    f.text(90,345,'原团三条边',size=21);f.text(405,345,'一个集合中转点，三条成员边',size=19)
    save('P7100',f,'成员费用分别二、五、一。新图一到二经过 S，仍支付二加五等于七；其它配对同样保持。')

    f=Figure('目标是整块挡板：落到内部时就已经到达',450)
    assert platform_walk([(1,4,10),(3,6,6)],0,1)==7
    f.line(200,100,380,100,BLUE,width=7);f.line(320,340,500,340,GREEN,width=7)
    arrow(f,205,85,375,85,BLUE);arrow(f,380,115,380,330,RED)
    for x,y in [(200,100),(380,100),(320,340),(500,340)]:f.circle(x,y,'',BLUE,radius=5)
    f.circle(380,340,'',GREEN,radius=7)
    f.text(200,65,'起点 x=1',size=19);f.text(390,92,'x=4',size=19)
    f.text(40,105,'高度 10',size=20);f.text(40,345,'高度 6',size=20)
    f.text(470,205,'行走 3，下落 4',size=21);f.text(470,245,'首次到目标：7',GREEN,size=22)
    f.text(325,380,'目标 [3,6]；绿色落点 x=4 在内部',size=20)
    f.text(45,427,'不必多走到左端 x=3，更不必走到右端 x=6',size=21)
    save('P10726',f,'这两块实际挡板的坐标与高度使用同一尺度。终点应接在内部落点，不能额外计目标板上的步行。')

    f=Figure('补丁会重新引入缺陷，缺陷数未必持续减少',365)
    states=['111','110','101','100','011','010','001','000'];costs=[1,1,1,2,1,1,1]
    for i,state in enumerate(states):
        row,col=divmod(i,4);f.box(35+180*col,80+125*row,125,55,state,GREEN if state=='000' else BLUE,size=23)
        if col<3:arrow(f,165+180*col,108+125*row,207+180*col,108+125*row,GRAY)
    f.text(190,158,'1',GRAY,size=18);f.text(370,158,'1',GRAY,size=18);f.text(550,158,'1',GRAY,size=18)
    f.text(190,283,'1',GRAY,size=18);f.text(370,283,'1',GRAY,size=18);f.text(550,283,'1',GRAY,size=18)
    f.text(45,184,'100 经第三补丁变 011，耗时 2',RED,size=20)
    f.text(40,339,'从左到右是缺陷 1、2、3；七次操作共花 8 秒',size=20)
    assert sum(costs)==8
    save('UVA658',f,'这组状态按样例补丁实际转移，1 表示缺陷存在。第三补丁消除缺陷一，却又加入缺陷二、三。')

    f=Figure('最便宜的演出不一定是每座城市的最优选择',350)
    for x,label,ticket,answer in [(90,1,6,6),(305,2,20,14),(520,3,1,1),(680,4,25,25)]:
        f.circle(x,175,label);f.text(x,110,'票 '+str(ticket),BLUE,size=20,anchor='middle');f.text(x,250,'答 '+str(answer),GREEN,size=20,anchor='middle')
    f.line(115,175,280,175,BLUE);f.line(330,175,495,175,BLUE)
    f.text(190,160,'往返 8',size=18,anchor='middle');f.text(412,160,'往返 14',size=18,anchor='middle')
    f.text(55,315,'二号选一号：6+8=14；选三号反而是 1+14=15',size=20)
    save('CF938D',f,'四号与其它城市不连通，保留本城票价；其它城市也须一起作为各自票价的初始源。')

    f=Figure('三乘三池塘、网边长二：覆盖次数不是距离',380)
    coverage=[[1,2,1],[2,4,2],[1,2,1]]
    for i,row in enumerate(coverage):
        for j,value in enumerate(row):f.box(65+85*j,80+85*i,80,80,value,GREEN if i==1 else BLUE,size=24)
    f.text(375,125,'选中间一行三个格子',GREEN,size=21)
    f.text(375,190,'覆盖次数和 2+4+2=8',size=21)
    f.text(375,255,'四种网位置，期望 8/4=2',size=20)
    f.text(55,365,'每个数字都由枚举四个二乘二窗口得到',size=21)
    save('CF912D',f,'绿色三个格子各放一条鱼，不合并同样覆盖两次的两个格子；覆盖和除以所有窗口数。')

    f=Figure('系数三、五：区间五到十只有七不可表示',305)
    values=[5,6,7,8,9,10];f.row(values,100,x=70,width=103,colors={i:RED if v==7 else GREEN for i,v in enumerate(values)})
    labels=['5','3+3','不可','3+5','3×3','5+5']
    for i,label in enumerate(labels):f.text(120+103*i,203,label,RED if i==2 else GREEN,size=19,anchor='middle')
    f.text(55,270,'按余数类的首个可达值计数，最后共有 5 个',size=21)
    save('P2371',f,'每格展示实际可表示性。前缀计数相减会排除区间外的零组合，七则没有非负整数组合。')

    f=Figure('横向与纵向分层，只有中间站能付费换层',395)
    f.line(110,130,420,130,BLUE,width=4);f.line(420,270,665,270,BLUE,width=4);f.line(420,130,420,270,RED,width=4)
    for x,y,label,c in [(110,130,'S',GREEN),(110,270,'S',GREEN),(420,130,'T',BLUE),(420,270,'T',BLUE),(665,130,'E',GRAY),(665,270,'E',GREEN)]:f.circle(x,y,label,c)
    f.text(35,115,'横',size=20);f.text(35,275,'纵',size=20)
    f.text(265,110,'两站：4 分钟',size=20,anchor='middle');f.text(545,310,'三站：6 分钟',size=20,anchor='middle')
    f.text(435,205,'换乘 1',RED,size=20);f.text(80,365,'S=(1,1)，T=(1,3)，E=(4,3)，共 4+1+6=11',size=20)
    save('P3831',f,'实际只在 T 换乘一次；上下两层的同名普通站不自动连通。起点任选层，终点任一层都可结束。')

    f=Figure('同样花一元到 X，可以保留更长的乘车前缀',370)
    lines=[[0,1],[0,2,2,2,1],[1,3]];assert fare_time(4,lines,0,3)=='2\n5'
    f.text(30,105,'线一',size=20);f.row(['A','X'],75,x=155,width=95)
    f.text(30,195,'线二',size=20);f.row(['A','Q','Q','Q','X'],165,x=155,width=95)
    f.text(30,285,'线三',size=20);f.row(['X','B'],255,x=155,width=95)
    f.text(400,110,'时间 1，票价 1',size=20);f.text(400,295,'再花 1 元、坐 1 分钟',size=20)
    f.text(40,348,'选线二再线三：总票价 2，总时间 4+1=5',GREEN,size=21)
    save('P6096',f,'线二三次停靠同一 Q 站，仍有五个真实出现位置；不能去重后把 A 到 X 的时间缩成二。')

    f=Figure('两条升序和列表，取走谁就推进谁',325)
    f.text(40,105,'a=1',size=21);f.row([3,6],75,x=200,width=125,colors={0:GREEN})
    f.text(40,195,'a=3',size=21);f.row([5,8],165,x=200,width=125,colors={0:GREEN})
    f.text(495,105,'加 b=[2,5]',size=20);f.text(495,195,'先取 3，再取 5',GREEN,size=20)
    f.text(40,285,'弹出 3 后，第一行推进到 6；第二行的 5 仍更小',size=21)
    save('UVA11997',f,'原数组为一、三与二、五，两行分别表示固定一个 a 后与 b 相加的有序列表；最小两项为三、五。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        first,separator,rest=spec.detail.partition('\n\n');spec.detail=first+block+(separator+rest if separator else '')
        spec.brief+=block
