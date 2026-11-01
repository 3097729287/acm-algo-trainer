"""Actual deletion graphs, blocked positions, subsets and cyclic switch moves."""
import base64
import hashlib
import json
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries


def lesson_figures(directory):
    f=Figure('位置是总重量，绿色表示该重量可以组成',390)
    for y,label,active in [(95,'只用一个 3',{0,3}),(235,'再用一个 3',{0,3,6})]:
        f.text(30,y-15,label,size=21)
        f.row(range(10),y,x=35,width=69,colors={i:GREEN if i in active else GRAY for i in range(10)})
    for old,new in [(0,3),(3,6)]:f.line(68+old*69,148,68+new*69,230,GREEN,width=3)
    f.text(45,355,'第二个 3 只能用一次；新出现的总重量是 6',size=22)
    f.save('bitset-states',directory)

    f=Figure('每项有三种位置，因此集合与子集配对共三的 n 次方',450)
    f.parts.append('<rect x="35" y="75" width="690" height="320" rx="12" fill="#fff" stroke="#68778b" stroke-width="2"/>')
    f.parts.append('<ellipse cx="435" cy="230" rx="245" ry="140" fill="#edf5ff" stroke="#2365ab" stroke-width="3"/>')
    f.parts.append('<ellipse cx="485" cy="255" rx="145" ry="80" fill="#edfff5" stroke="#12805c" stroke-width="3"/>')
    f.text(400,120,'S = {1,2,4}',BLUE,size=24,anchor='middle');f.text(485,210,'sub = {2,4}',GREEN,size=22,anchor='middle')
    for x,y,label,color in [(115,150,0,GRAY),(115,320,3,GRAY),(265,220,1,BLUE),(420,275,2,GREEN),(555,275,4,GREEN)]:f.circle(x,y,label,color)
    f.text(45,435,'灰色不在 S；蓝色只在 S；绿色还在子集 sub 中',size=22)
    f.save('subsets',directory)

    f=Figure('异号相加先比较绝对值，结果取较大者的符号',370)
    f.box(55,95,180,60,'−8',RED);f.box(305,95,180,60,'+12',BLUE);f.box(560,95,145,60,'+4',GREEN)
    f.text(265,133,'+',size=30,anchor='middle');f.text(525,133,'=',size=30,anchor='middle')
    f.box(55,225,180,60,'−8',RED);f.box(305,225,180,60,'+5',BLUE);f.box(560,225,145,60,'−3',RED)
    f.text(265,263,'+',size=30,anchor='middle');f.text(525,263,'=',size=30,anchor='middle')
    f.text(45,345,'存绝对值数字串与符号，零统一规范为非负',size=23)
    f.save('decimal-signed',directory)


def attach_figures(specs):
    lesson_figures(ROOT/'docs/foundations/assets')
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf-8'))}
    def save(pid,f,caption):
        p=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode();key='assets/core7/'+pid+'.svg';old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)
    from core7_cases_subset_dp import coin_vectors,bird_fraction_cover

    f=Figure('同样两条边，先删中点与先删端点的费用不同',370)
    for x,y in [(140,145),(380,145),(620,145)]:f.circle(x,y,{140:1,380:2,620:3}[x],BLUE)
    f.line(165,145,355,145,BLUE);f.line(405,145,595,145,BLUE)
    f.text(260,125,'权 2',size=24,anchor='middle');f.text(500,125,'权 5',size=24,anchor='middle')
    f.text(55,245,'先删 2：两条同时删，费用 2×(2+5)=14',RED,size=23)
    f.text(55,310,'先删两端：分别付 2、5，最后孤点免费，总费 7',GREEN,size=22)
    save('P12593',f,'真实三点链只有两条带权边，删除端点后中点只剩一条边，费用的乘数随余图改变。')

    f=Figure('按第二个按钮，再按第一个，三盏灯全部关闭',455)
    for y,values,label in [(85,[1,1,1],'初始'),(225,[1,0,1],'按钮 2 后'),(365,[0,0,0],'按钮 1 后')]:
        f.text(35,y+30,label,size=21);f.row(values,y,x=250,width=130,colors={i:GREEN if not v else BLUE for i,v in enumerate(values)})
    f.text(175,185,'按钮 2：强制开灯 1、关灯 2',size=22)
    f.text(175,325,'按钮 1：强制关灯 1、3',size=22)
    save('P2622',f,'采用原样例两按钮的真实效果，零位为关；已经关闭的灯再遇关灯操作仍关闭，不会反向打开。')

    f=Figure('只禁止长度四的回文；短一些的重复仍允许',385)
    f.text(40,85,'原样例：AB?A?BA，K=4',size=23)
    f.row(list('ABAAABA'),110,x=60,width=90)
    f.text(60,185,'ABAAABA：四个长度四窗口都不回文',GREEN,size=22)
    f.row(list('ABBABBA'),245,x=60,width=90,colors={i:RED for i in range(4)})
    f.text(60,335,'ABBABBA：最前 ABBA 回文，这次填法作废',RED,size=22)
    save('AT_abc359_d',f,'两排均为同一原串的实际问号替换；绿色说明的是全部定长窗口，红色首四格明确标出一个禁止窗口。')

    f=Figure('去掉一枚 2 后，正重量是一、二、三',390)
    f.row([1,2,2],90,x=130,width=170,colors={2:RED});f.line(475,85,630,150,RED,width=4)
    f.text(60,230,'保留 {1,2}：只用 1、只用 2、两者都用',size=23)
    f.row([1,2,3],275,x=130,width=170,colors={0:GREEN,1:GREEN,2:GREEN})
    f.text(60,365,'空集重量 0 不计；三种重量，不按不同组成重复计数',size=21)
    save('P1441',f,'上排是三枚真实砝码，叉去的是第三枚；下排列出保留者能实际称出的全部正重量。')

    f=Figure('一条跨一号到四号位置的边，付三个分界的费用',400)
    for x in [210,370,530]:f.line(x,85,x,310,GRAY,dash=True,width=2)
    for i,x in enumerate([130,290,450,610]):f.circle(x,255,i+1,BLUE)
    f.line(130,230,130,125,GREEN);f.line(130,125,610,125,GREEN,width=5);f.line(610,125,610,230,GREEN)
    f.text(55,350,'绿色这一条边跨过三条虚线，线路长度为 3',GREEN,size=23)
    f.text(55,390,'若四头牛互为朋友，全部六条边总长为 10',size=22)
    save('P2210',f,'只突出四点完全朋友图的一条边，其它边仍需各自计费；三个虚线是队列相邻位置之间的实际分界。')

    f=Figure('同批重量相加、时间取最大，前后两批时间相加',400)
    f.box(40,85,430,190,'',BLUE,fill='#f7fbff');f.box(510,85,210,190,'',GREEN,fill='#f5fff9')
    f.box(70,115,165,60,'1：重60、时24',BLUE,size=18);f.box(265,115,165,60,'2：重40、时10',BLUE,size=18)
    f.box(530,115,170,60,'3：重50、时18',GREEN,size=18)
    f.text(255,230,'总重 100，耗时 24',BLUE,size=23,anchor='middle');f.text(615,230,'耗时 18',GREEN,size=23,anchor='middle')
    f.text(55,335,'桥限重 100：先送 {1,2}，再送 {3}，总时 24+18=42',size=21)
    save('P5911',f,'采用原样例三位队员，两个边框分别是真实的一批；第一批的一百总重不超限，但耗时不是二十四加十。')

    f=Figure('覆盖一格只抓一条，重复爆炸仍可能必要',470)
    originX,originY,cell=55,95,60
    covered={(0,0),(0,1),(0,2),(1,1)}
    for r in range(5):
        for c in range(5):f.box(originX+c*cell,originY+r*cell,cell-2,cell-2,'',GREEN if (r,c) in covered else GRAY,fill='#edfff5' if (r,c) in covered else '#fff')
    for r,c,count in [(0,0,2),(1,1,1),(4,4,2)]:f.text(originX+c*cell+28,originY+r*cell+36,count,BLUE,size=28,anchor='middle')
    f.text(originX+cell+28,originY+36,'×',RED,size=28,anchor='middle')
    for y,note in [(125,'在 (1,2) 炸两次'),(190,'(1,1)：2→1→0'),(245,'(2,2)：1→0→0'),(315,'远处 (5,5) 另炸两次'),(380,'总共 4 次')]:f.text(390,y,note,GREEN if y==380 else BLUE,size=21)
    f.text(55,445,'绿色是边界内的十字覆盖，× 为投弹中心；数字是鱼数',size=21)
    save('P10865',f,'原五乘五样例的三个鱼格，投弹中心按行列记为(1,2)；第一次后左上仍剩一条，第二次才清空。')

    assert coin_vectors([1,2,5,10],[3,2,3,1],10)==4
    f=Figure('十元方案：扣单类超限，补回同时超限的交集',590)
    f.parts.append('<rect x="35" y="75" width="690" height="445" rx="12" fill="#fff" stroke="#68778b" stroke-width="2"/>')
    f.parts.append('<ellipse cx="270" cy="245" rx="175" ry="125" fill="#fff4f5" fill-opacity="0.3" stroke="#bc3645" stroke-width="3"/>')
    f.parts.append('<ellipse cx="490" cy="245" rx="175" ry="125" fill="#edf5ff" fill-opacity="0.3" stroke="#2365ab" stroke-width="3"/>')
    f.text(240,110,'A：1元币超过3枚',RED,size=20,anchor='middle');f.text(535,110,'B：2元币超过2枚',BLUE,size=20,anchor='middle')
    for x,y,label in [(215,185,'10,0,0,0'),(190,230,'8,1,0,0'),(190,285,'6,2,0,0'),(265,335,'5,0,1,0'),(400,245,'4,3,0,0'),(565,205,'2,4,0,0'),(565,285,'0,5,0,0'),(230,430,'3,1,1,0'),(530,430,'1,2,1,0'),(230,485,'0,0,2,0'),(530,485,'0,0,0,1')]:
        f.circle(x-60,y-5,'',GREEN if y>=430 else GRAY,radius=4);f.text(x,y,label,GREEN if y>=430 else BLUE,size=17,anchor='middle')
    f.text(55,560,'每串是四类枚数；11−5−3+1=4，绿色四份合法',GREEN,size=22)
    save('P1450',f,'实际列出面值1、2、5、10且总额十的全部十一份枚数清单，A有五份、B有三份、交集一份，外侧四份满足原库存。')

    f=Figure('模式 a?、?b、??：恰好匹配两个的有五十串',450)
    f.parts.append('<rect x="40" y="80" width="680" height="295" rx="12" fill="#fff" stroke="#68778b" stroke-width="2"/>')
    f.parts.append('<ellipse cx="270" cy="220" rx="165" ry="115" fill="#edfff5" fill-opacity="0.3" stroke="#12805c" stroke-width="3"/>')
    f.parts.append('<ellipse cx="490" cy="220" rx="165" ry="115" fill="#edfff5" fill-opacity="0.3" stroke="#12805c" stroke-width="3"/>')
    f.text(220,125,'a? 匹配区',BLUE,size=22,anchor='middle');f.text(545,125,'?b 匹配区',BLUE,size=22,anchor='middle')
    f.text(215,215,'ac、ad…',GREEN,size=24,anchor='middle');f.text(215,265,'25 串',GREEN,size=25,anchor='middle')
    f.text(545,215,'zb、yb…',GREEN,size=24,anchor='middle');f.text(545,265,'25 串',GREEN,size=25,anchor='middle')
    f.text(380,225,'ab',RED,size=25,anchor='middle');f.text(380,265,'匹配3个',RED,size=18,anchor='middle')
    f.text(70,355,'整个边框都匹配 ??；两圈外的 625 串只匹配 1 个',size=20)
    f.text(55,425,'ab 的容斥权重：三个双交集各 +1，三交集 −3，抵消',size=20)
    save('P2167',f,'两个椭圆是第一字符固定a与第二字符固定b的真实字符串集合，交集只有ab；外框代表第三个全问号模式。')

    f=Figure('首轮看到负一的前提宝物，仍可能值得吃',505)
    f.box(245,70,270,55,'还剩 2 次，尚未解锁',BLUE)
    f.line(380,125,205,180,BLUE);f.line(380,125,570,180,GRAY)
    f.box(105,180,200,55,'看到 A，吃得 −1',GREEN,size=20);f.box(460,180,235,55,'看到 B，尚不能吃',GRAY,size=20)
    f.line(205,235,110,310,GREEN);f.line(205,235,320,310,GREEN)
    f.box(35,310,150,55,'再来 A：放弃',BLUE,size=18);f.box(245,310,150,55,'再来 B：+100',GREEN,size=18)
    f.text(110,405,'总分 −1',size=22,anchor='middle');f.text(320,405,'总分 99',GREEN,size=22,anchor='middle');f.text(575,345,'之后最优也只得 0',GRAY,size=20,anchor='middle')
    f.text(45,470,'每次 A、B 各半：首轮吃 A 的条件期望 49，全局为 24.5',size=20)
    save('P2473',f,'A负一且无前提，B一百且要求吃过A；四叶的原始观察概率均等，图右支的两种后续都无法获得正分。')

    points=[(100,300),(200,400),(300,300)];assert bird_fraction_cover(points)==1
    f=Figure('三点落在同一下开口轨迹，一发全部经过',505)
    f.line(70,420,650,420,GRAY);f.line(80,435,80,65,GRAY)
    for x in range(5):f.text(80+125*x,450,x,size=18,anchor='middle')
    for y in range(1,5):f.text(60,427-75*y,y,size=18,anchor='middle')
    curve=' '.join(f'{80+125*x:.2f},{420-75*(-x*x+4*x):.2f}' for x in [i/40 for i in range(161)])
    f.parts.append(f'<polyline points="{curve}" fill="none" stroke="{GREEN}" stroke-width="4"/>')
    for x,y in [(1,3),(2,4),(3,3)]:f.circle(80+125*x,420-75*y,'',BLUE,radius=10);f.text(80+125*x+15,410-75*y,f'({x},{y})',BLUE,size=20)
    f.text(390,270,'y = −x² + 4x',GREEN,size=25)
    f.text(45,490,'原点自动在曲线上；两点确定轨迹，再检查全部猪',size=22)
    save('P2831',f,'横纵轴用原坐标单位，一三、二四、三三三只猪都在同一条真实下开口曲线上，原点是弹弓而不是猪。')

    f=Figure('目标块固定后，只有原位置不符的两个人离队',405)
    for i in range(6):f.text(100+105*i,75,i+1,GRAY,size=18,anchor='middle')
    f.row([1,2,1,2,1,2],100,x=50,width=105,colors={1:RED,4:RED})
    f.row([1,1,1,2,2,2],255,x=50,width=105,colors={1:GREEN,4:GREEN})
    f.line(205,155,520,250,RED,width=3);f.line(520,155,205,250,GREEN,width=3)
    f.text(45,355,'只让原第 2、5 个位置的人出来，再填这两个空位',size=22)
    f.text(45,395,'其余四人保持原位置；费用是 2 人，不是相邻交换数',size=21)
    save('P3694',f,'格内数字是乐队编号，上方小字才是位置编号；两条斜线连接离队者前后所填空位，两人都要计入费用。')

    f=Figure('同时换位后没有同格，不能把途中交叉判成碰撞',440)
    f.text(35,110,'时刻 1',size=22);f.text(35,295,'时刻 2',size=22)
    for y,values in [(85,['萃香','大瓜']),(270,['大瓜','萃香'])]:f.row(values,y,x=200,width=210,colors={i:GREEN if label=='萃香' else RED for i,label in enumerate(values)})
    f.line(300,140,510,265,GREEN,width=4);f.line(510,140,300,265,RED,width=4)
    f.text(45,370,'一行两格，无小瓜：必须从左移到右，最少移动 1 次',size=21)
    f.text(45,425,'线段仅连接时刻端点，西瓜的瞬移途中不占位',size=22)
    save('P3786',f,'时刻一萃香在左、大瓜在右，下一刻双方交换格子；只检查每个时刻最终同格，图示方案始终安全。')

    f=Figure('最高分顺序由完成时刻决定，不能先贪歌名字典序',440)
    for i,(start,length,label,color) in enumerate([(0,2,'S3',GREEN),(2,3,'S1',BLUE),(5,1,'S2',GRAY)]):
        f.box(75+70*start,115,70*length-3,70,label,color)
        end=start+length;f.text(75+70*end,225,f'时刻 {end}',color,size=20,anchor='middle')
    f.text(75,95,'开始 0',size=20)
    f.text(60,295,'S3：5−2=3；S1：8−5=3；S2：过期得 0',size=23)
    f.text(60,355,'总用时 6≤10，总分 6≥奖励线 2',GREEN,size=24)
    f.text(60,415,'S编号按原输入行；比较字典序时使用完整歌名',size=22)
    save('P3947',f,'原样例的实际时间线：SnowHalation后接BokutachiwaHitotsunoHikari，再唱Korekara，三段时长为二三一。')

    f=Figure('洗一天表示隔一天再穿，不能第二天立即重复',465)
    f.text(35,85,'天数',size=22)
    for i in range(5):f.text(215+100*i,85,i+1,size=22,anchor='middle')
    for y,label,values in [(115,'衣服',[1,2,1,2,1]),(225,'天气',[2,4,3,5,2]),(335,'收益',[10,40,15,50,10])]:
        f.text(35,y+32,label,size=22);f.row(values,y,x=170,width=100,colors={i:GREEN if i%2 else BLUE for i in range(5)})
    f.text(45,440,'颜色 5、10，清洗都为 1；此安排总收益 125',GREEN,size=23)
    save('P4928',f,'原五天样例的一份最优安排；衣服一在一三五天、衣服二在二四天，每次使用间隔两天。')

    f=Figure('字母表 a、b、c：听到 abac 至少唱两遍',380)
    f.row(list('abcabc'),110,x=65,width=105,colors={0:GREEN,1:GREEN,2:GRAY,3:GREEN,4:GRAY,5:GREEN})
    f.line(65+3*105-2,80,65+3*105-2,230,RED,dash=True)
    f.text(210,240,'第一遍',BLUE,size=23,anchor='middle');f.text(535,240,'第二遍',BLUE,size=23,anchor='middle')
    f.text(45,310,'绿色为听到的字母；b 后再听到 a，必须开始下一遍',size=21)
    f.text(45,365,'同一个字母在每遍只有一次，连续相同也要重新开始',size=21)
    save('P7296',f,'实际唱两遍abc，漏听第一遍c及第二遍b便得到abac；两个a已经说明一遍绝不够。')

    f=Figure('两步后灯全灭，即使最后开关还有活跃位也成功',565)
    f.text(270,80,'灯',BLUE,size=24,anchor='middle');f.text(565,80,'右旋后的开关',BLUE,size=23,anchor='middle')
    for y,light,switch,label in [(105,'111','000','初始'),(285,'011','010','第1步后'),(465,'000','101','第2步后')]:
        f.text(30,y+31,label,size=20);f.row(list(light),y,x=155,width=80,colors={i:GREEN if c=='0' else BLUE for i,c in enumerate(light)});f.row(list(switch),y,x=450,width=80)
    f.text(55,235,'翻开关第 1 位得100，翻灯得011，再右旋成010',size=21)
    f.text(55,415,'翻开关第 3 位得011，翻灯得000，再右旋成101',size=21)
    save('P9017',f,'三位均从字符串左起编号，初始灯111、开关000，依原协议次序操作两步；最终101是开关，灯已经000。')

    f=Figure('四点完全图：四个三角环、三个四边环，共七个',485)
    points=[(220,120),(540,120),(540,340),(220,340)]
    for u,v in [(0,1),(1,2),(2,3),(3,0),(0,2),(1,3)]:f.line(*points[u],*points[v],GREEN if (u,v) in [(0,1),(1,2),(2,3),(3,0)] else GRAY,dash=(u,v) in [(0,2),(1,3)],width=4)
    for i,p in enumerate(points):f.circle(*p,i+1,BLUE)
    f.text(50,415,'1→2→3→4 与 1→4→3→2 是同一个无向环',size=22)
    f.text(50,465,'固定最小起点后，仍须把正反方向的重复除以二',size=22)
    save('CF11D',f,'绿色为其中一个四边简单环，虚线弦边不影响它的合法性；点一是此环唯一允许的起点。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n';spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
