"""Actual item sets, continuous gaps, signed coordinates and FIFO operations."""
import base64
import hashlib
import json
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries


def attach_figures(specs):
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf-8'))}
    def save(pid,f,caption):
        p=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode();key='assets/core7/'+pid+'.svg';old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)
    def balls(f,values,y,x=125,step=110,color=BLUE):
        for i,v in enumerate(values):f.circle(x+i*step,y,v,color)

    f=Figure('只有一株药，时间够两次也不能重复采',355)
    f.text(55,92,'总时间 4；唯一草药：耗时 2，价值 3',size=23)
    f.row([0,0,3,3,3],135,x=65,width=125,colors={2:GREEN,3:GREEN,4:GREEN})
    for i in range(5):f.text(125+i*125,225,'上限 '+str(i),GRAY,size=20,anchor='middle')
    f.text(65,290,'倒序：最大价值 3',GREEN,size=24)
    f.text(65,335,'正序会把同株重复加入，错误得到 6',RED,size=23)
    save('P1048',f,'五格分别对应时间上限零至四；每株只取一次，所以容量四仍是价值三。')

    f=Figure('三道三分钟的题不能劈开，两脑分配三与六',365)
    f.text(55,100,'左脑',BLUE,size=23);f.row([3],65,x=180,width=155)
    f.text(55,225,'右脑',GREEN,size=23);f.row([3,3],190,x=180,width=155,colors={0:GREEN,1:GREEN})
    f.text(65,310,'一科总时长 9；可达半边 3；本科用 9−3=6',size=23)
    f.text(65,350,'每题整体分配，不能把总时长直接平分',RED,size=22)
    save('P2392',f,'每个方块是一整道三分钟题；右脑依次做两道题，等到第六分钟这科才结束。')

    f=Figure('十七拆成十六与一，只需要两个四次方',320)
    balls(f,[16,1],130,x=255,step=250,color=GREEN)
    f.text(255,215,'2 的四次方',size=23,anchor='middle');f.text(505,215,'1 的四次方',size=23,anchor='middle')
    f.text(65,285,'同一个四次方允许重复，例如三等于三个一',size=23)
    save('P1679',f,'两圆对应两项而非两个底数相加，十六加一才是目标十七。')

    f=Figure('两种预算都必须满足，不能只检查其中一种',400)
    f.text(55,95,'金钱、时间上限均为 3',size=24)
    for y,label,values,color in [(135,'愿望 A',[1,3],BLUE),(215,'愿望 B',[3,1],BLUE),(295,'A 与 B',[4,4],RED)]:
        f.text(55,y+30,label,color,size=23);f.row(values,y,x=270,width=175,colors={0:color,1:color})
    f.text(300,385,'金钱',GRAY,size=22);f.text(480,385,'时间',GRAY,size=22)
    save('P1855',f,'A和B单独都合法，一起则两种消耗都超过三，最多完成一个愿望。')

    f=Figure('同重的两捆可以各取一次，不能去重成一捆',350)
    balls(f,[6,5,5],125,x=160,step=220)
    f.line(380,170,380,235,GREEN,width=4);f.line(600,170,600,235,GREEN,width=4)
    f.text(490,275,'5 + 5 = 10，恰好到容量',GREEN,size=25,anchor='middle')
    f.text(65,325,'重量 6 的那捆不取；不能拆捆，也不能重复拿同捆',size=21)
    save('P2639',f,'圆表示三捆独立草料，两个五虽然数字相同，仍然是两件可各取一次的物品。')

    f=Figure('十二不是先拿九，三个四能少用一项',350)
    balls(f,[9,1,1,1],120,x=110,step=150,color=RED)
    f.text(690,130,'4 项',RED,size=23,anchor='middle')
    balls(f,[4,4,4],245,x=185,step=170,color=GREEN)
    f.text(65,325,'所有圆内数字均为平方数；下排只需 3 项',size=23)
    save('P11246',f,'两排的总和都是十二；比较项数后，四加四加四优于九加一加一加一。')

    f=Figure('达到一百毫升后，更多容量合并到同一达标状态',365)
    f.row([60,50],100,x=170,width=200,colors={0:BLUE,1:GREEN})
    f.text(270,200,'售价 4',BLUE,size=23,anchor='middle');f.text(470,200,'售价 3',GREEN,size=23,anchor='middle')
    f.text(65,270,'合计 110 毫升，费用 7；状态记为容量 100',GREEN,size=24)
    f.text(65,335,'单瓶都未达标；允许超过，不要求恰好一百',size=22)
    save('B3873',f,'两瓶分别六十和五十毫升，购买后的实际容量一百一十，但压缩状态为需求一百。')

    f=Figure('一个划分被两个互补子集各统计一次',355)
    f.row([1,2],95,x=95,width=160,colors={0:BLUE,1:BLUE});f.row([3],95,x=505,width=160,colors={0:GREEN})
    f.text(255,225,'集合和 3',BLUE,size=24,anchor='middle');f.text(585,225,'集合和 3',GREEN,size=24,anchor='middle')
    f.text(65,295,'选左边与选右边是同一组划分，最后计数除二',size=23)
    save('P1466',f,'N等于三，两个集合互不相交且覆盖一二三，交换集合顺序不产生新的划分。')

    f=Figure('目标四人，两个整体为三与五，平局选择三',380)
    balls(f,[1,2,3],115,x=120,step=80,color=BLUE)
    balls(f,[4,5,6,7,8],225,x=250,step=80,color=GREEN)
    for x1,x2 in [(120,200),(200,280)]:f.line(x1+30,115,x2-30,115,BLUE,width=3)
    for x1,x2 in [(250,330),(330,410),(410,490),(490,570)]:f.line(x1+30,225,x2-30,225,GREEN,width=3)
    f.text(470,120,'整体 3 人',BLUE,size=24)
    f.text(65,320,'可选人数为 0、3、5、8；3 与 5 距目标同为 1',size=22)
    f.text(65,365,'平局取较少人数：答案 3',GREEN,size=24)
    save('P2170',f,'线表示实力相当关系，三人链和五人链分别形成两个不可拆的连通块。')

    f=Figure('邮资六可以贴出，也不能越过邮资五的缺口',355)
    f.text(55,95,'面额 1、3，最多 2 张',size=24)
    f.row([1,2,3,4,5,6],135,x=55,width=105,colors={0:GREEN,1:GREEN,2:GREEN,3:GREEN,4:RED,5:BLUE})
    for i,label in enumerate(['1','1+1','3','3+1','需 3 张','3+3']):f.text(105+i*105,255,label,RED if i==4 else GRAY,size=21,anchor='middle')
    f.text(65,325,'连续区间只到 4；不能把最大可达的 6 当答案',size=23)
    save('P2725',f,'格子顺序就是一至六的邮资，五需要三张超过限制，导致连续覆盖在四处停止。')

    f=Figure('每个英雄各买三款：费用相加，展示选择相乘',370)
    f.row([3,3,3],105,x=110,width=180,colors={0:BLUE,1:GREEN,2:BLUE})
    for i in range(3):f.text(200+180*i,230,'费用 6',size=23,anchor='middle')
    f.text(65,295,'每款 2 元，总费用 18；展示方式 3×3×3=27',size=23)
    f.text(65,350,'目标至少 24，不需要乘积恰好等于 24',GREEN,size=23)
    save('P5365',f,'原样例的三个英雄各有四款可买，这里各选三款便达到至少二十四种展示方式。')

    f=Figure('金币上限大，改记每个攻击力的最少费用',370)
    f.row([99,33,11],100,x=110,width=180,colors={0:GREEN,1:GREEN,2:GRAY})
    for i,c in enumerate([1,2,3]):f.text(200+180*i,225,'价格 '+str(c),size=23,anchor='middle')
    f.text(65,295,'预算 5：买前两件，攻击力 132，费用 3',GREEN,size=24)
    f.text(65,350,'三件全买需 6，超预算；不用把金币恰好花完',size=22)
    save('P14920',f,'每格是单件攻击力，下面标单价；三金币即可得到最优的一百三十二点，不要求花光五金币。')

    f=Figure('刚好第十时刻仍可用垃圾，垫高或吃掉二选一',410)
    f.text(55,95,'初始死亡时刻 10；垃圾在时刻 10 落下',size=23)
    f.row(['垫高 10','吃掉 +30'],150,x=95,width=280,colors={0:GREEN,1:BLUE})
    f.text(235,280,'井深 10：立即出井',GREEN,size=22,anchor='middle')
    f.text(515,325,'死亡时刻改为 40',BLUE,size=22,anchor='middle')
    f.text(65,390,'两条分支只选一条；不可同件先吃再垫',RED,size=23)
    save('P1156',f,'同一件垃圾的高度十、食物三十，等于死亡时刻也允许使用，垫高分支在时刻十逃出。')

    from core7_cases_knapsack import subsets
    assert set(subsets([1,2,4,6]))==set(range(14))
    f=Figure('十三件拆成四批，整批选取仍能覆盖所有件数',360)
    f.row([1,2,4,6],100,x=75,width=150,colors={3:GREEN})
    f.text(65,235,'前三批能取 0 到 7 件；加最后一批得到 6 到 13 件',size=22)
    f.text(65,295,'两段覆盖 0 到 13，不漏数量，也不会超过 13',GREEN,size=23)
    f.text(65,345,'每批的重量、价值都乘上批内件数',size=22)
    save('P1776',f,'四格是整批件数，不是单件重量；一二四与剩余六的组合覆盖零到十三。')

    f=Figure('长度先为负，仍可接上后一个魔法达到正目标',365)
    balls(f,[-3,4],135,x=220,step=320)
    f.line(260,135,500,135,GREEN,width=4);f.text(380,105,'附加威力 7',GREEN,size=22,anchor='middle')
    f.text(220,235,'基础威力 10',size=23,anchor='middle');f.text(540,235,'基础威力 20',size=23,anchor='middle')
    f.text(65,305,'按编号 1→2：总长度 1，威力 10+20+7=37',size=23)
    f.text(65,350,'第一个魔法没有前驱附加值；只算相邻影响',size=22)
    save('P4912',f,'圆内是咒语长度，编号按从左到右递增；保留负三长度状态才能得到目标一的合法组合。')

    f=Figure('负差与正差抵消，酸甜总和作为收益保留',390)
    f.row(['酸 1 甜 2','酸 2 甜 1'],110,x=95,width=280,colors={0:BLUE,1:GREEN})
    f.text(235,250,'差 −1，收益 3',BLUE,size=23,anchor='middle')
    f.text(515,250,'差 +1，收益 3',GREEN,size=23,anchor='middle')
    f.text(65,325,'一起选：酸 3、甜 3，差为零，总风味 6',size=24)
    f.text(65,375,'差值可以为负，不能把负下标状态丢掉',RED,size=22)
    save('P13018',f,'每份食材的酸与甜分别相加；差值相消后平衡，目标收益仍是两种味道总量。')

    from core7_cases_knapsack import fifo_score
    assert fifo_score([-9,5,6],[0,0,1],[0,1,2])==11
    assert fifo_score([-9,5,6],[0,0,1],[1,2])==6
    f=Figure('被删除的负分格子也要写进选择过程',455)
    f.row([-9,5],95,x=185,width=150,colors={0:RED,1:BLUE})
    f.text(55,185,'先选 1、2',size=22);f.text(550,130,'队首在左',GRAY,size=21)
    f.row([-9,5,6],235,x=110,width=175,colors={0:RED,1:GREEN,2:GREEN})
    f.line(130,250,265,295,RED,width=4);f.line(130,295,265,250,RED,width=4)
    f.text(65,360,'再选 3，先删一个旧格子：最终留下 5、6，得 11',size=22)
    f.text(65,415,'若只输出 2、3，会把 5 删掉，只剩 6 分',RED,size=23)
    save('P11274',f,'三格的删除数为零、零、一；完整输出一二三与仅输出最终保留的二三有不同执行结果。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n';spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
