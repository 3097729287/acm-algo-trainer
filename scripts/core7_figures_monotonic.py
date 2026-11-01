"""Concrete stacks, windows, towers and time-graph examples."""
import base64,hashlib,json
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries

def lesson_figures(directory):
    f=Figure('4、1、6：首个更大位置与滑窗极值是不同答案',455)
    f.row([4,1,6],100,x=135,width=160)
    f.text(45,230,'位置答案：3、3、0；6 到来时解决前两项',GREEN,size=23)
    f.box(60,290,285,60,'窗口 [4,1] 最大为 4',BLUE,size=21);f.box(390,290,300,60,'窗口 [1,6] 最大为 6',GREEN,size=21)
    f.text(45,415,'栈等答案被解决；队列删去更差且更早过期的候选',size=22)
    f.save('monotone-structures',directory)

    f=Figure('区间最小值交给最右相等项：总和为十三',480)
    for y,label,values in [(90,'数值',[3,1,2,1]),(200,'负责区间数',[1,4,1,4]),(310,'贡献',[3,4,2,4])]:
        f.text(30,y+32,label,size=22);f.row(values,y,x=210,width=125,colors={1:GREEN,3:GREEN})
    f.text(45,410,'整段 [3,1,2,1] 归第四项，不再归第二项',size=23)
    f.text(45,460,'四项贡献：3+4+2+4=13',GREEN,size=24)
    f.save('monotone-contribution',directory)

def attach_figures(specs):
    lesson_figures(ROOT/'docs/foundations/assets')
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text(encoding='utf-8'))}
    def save(pid,f,caption):
        p=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode();key='assets/core7/'+pid+'.svg';old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)

    f=Figure('前缀 k：排序后仍要保留两个 ki',370)
    f.row(['na','no','ki','ki','ka','ku'],100,x=35,width=115,colors={0:GRAY,1:GRAY,2:GREEN,3:GREEN,4:GREEN,5:GREEN})
    f.row(['ka','ki','ki','ku'],240,x=100,width=150,colors={i:GREEN for i in range(4)})
    f.text(45,345,'先筛选首部匹配，再对这些出现逐个排序，不去重',size=23)
    save('P1628',f,'原样例六个词中有四次匹配，重复ki代表两个输入词，两个都要输出。')

    f=Figure('小值域次数表直接还原年龄顺序',390)
    f.row([2,3,2,3,1],90,x=55,width=130)
    f.text(45,220,'1 岁：1 人；2 岁：2 人；3 岁：2 人',size=24)
    f.row([1,2,2,3,3],280,x=55,width=130,colors={i:GREEN for i in range(5)})
    save('UVA11462',f,'原第二组样例按年龄次数展开；示例只出现三种年龄，程序仍遍历完整一至九十九岁值域。')

    f=Figure('加入 2、1、3、5、4 后的严格后缀纪录',535)
    for x,label in [(110,'加入值'),(360,'纪录下标'),(650,'异或')]:f.text(x,85,label,size=23,anchor='middle')
    for i,(value,indices,xor) in enumerate([(2,'1',1),(1,'1、2',3),(3,'3',3),(5,'4',4),(4,'4、5',1)]):
        y=150+i*75;f.text(110,y,value,size=25,anchor='middle');f.text(360,y,indices,GREEN,size=25,anchor='middle');f.text(650,y,xor,BLUE,size=25,anchor='middle')
    save('B3666',f,'与原样例五行输出对应，最后纪录值是五与四，但异或的是下标四与五，结果一。')

    f=Figure('m=2：第三项前面只看 7、8，不含当前的 1',420)
    f.row([7,8,1,4,3,2],100,x=35,width=115,colors={0:GREEN,1:GREEN,2:RED,3:GRAY,4:GRAY,5:GRAY})
    f.text(45,230,'第三行答案 7；若提前加入当前 1 就会错误变成 1',size=22)
    f.row([0,7,7,1,1,3],300,x=35,width=115,colors={i:GREEN for i in range(6)})
    f.text(45,395,'完整输出：先查询之前至多两项，再加入当前项',size=22)
    save('P1440',f,'原样例的查询与当前项分开标色，首项无前驱输出零，第三项之前的最小值仍为七。')

    f=Figure('长度三的完整窗口：当前右端也参与极值',460)
    f.row([1,3,-1,-3,5,3,6,7],90,x=30,width=88,colors={0:GREEN,1:GREEN,2:GREEN})
    f.text(45,220,'首窗 [1,3,−1]：最小 −1，最大 3',size=23)
    f.text(45,285,'次窗 [3,−1,−3]：最小 −3，最大 3',size=23)
    f.text(45,360,'全部最小：−1、−3、−3、−3、3、3',GREEN,size=23)
    f.text(45,425,'全部最大：3、3、5、5、6、7',BLUE,size=23)
    save('P1886',f,'原样例八项给出六个完整窗口，尚未读满三项时不输出。')

    f=Figure('等分保留较新的产品，最低分不会改变',395)
    f.row([16,5,6,9,5],100,x=55,width=130,colors={1:GRAY,4:GREEN})
    f.text(45,235,'窗口 [16,5,6,9] 最低 5',size=24)
    f.text(45,300,'移到 [5,6,9,5] 仍最低 5，可用较新的第 5 件',GREEN,size=23)
    f.text(45,365,'只比大小不能判断过期，候选必须保存位置',size=22)
    save('P2251',f,'原样例的前两个四项窗口，重复分五来自不同产品，新位置能够替代更早到期的位置。')

    f=Figure('最近且严格更高：两个高度一都看向第六头',410)
    f.row([3,2,6,1,1,2],100,x=35,width=115)
    f.text(45,225,'上方按顺序为六头牛的实际身高',size=22)
    f.row([3,3,0,6,6,0],285,x=35,width=115,colors={i:GREEN for i in range(6)})
    f.text(45,385,'下方是目标编号；高度相同的相邻牛不能互相仰望',size=22)
    save('P2947',f,'原样例逐项对齐身高与答案，三号身高六已最高，六号右侧无人，两者输出零。')

    f=Figure('当前值 3 到来时，只解决较小的待回答位置',425)
    f.row([1,4,2,3,5],95,x=55,width=130,colors={2:RED,3:GREEN})
    f.text(45,220,'第 4 项值 3：第 3 项值 2 的答案为下标 4',size=23)
    f.row([2,5,4,5,0],285,x=55,width=130,colors={i:GREEN for i in range(5)})
    f.text(45,395,'最后的 5 没有更大右邻，答案为 0',size=23)
    save('P5788',f,'原样例对应的五个首个更大位置；红色二被当前三解决，栈里更大的四继续等待。')

    f=Figure('费用一的车道放两辆 b=2 的车，费用二放单辆',445)
    f.box(40,110,680,90,'',GREEN);f.circle(300,155,'车2',GREEN,radius=32);f.circle(470,155,'车3',GREEN,radius=32);f.text(75,160,'单价 1',GREEN,size=24)
    f.box(40,255,680,90,'',BLUE);f.circle(385,300,'车1',BLUE,radius=32);f.text(75,305,'单价 2',BLUE,size=24)
    f.text(45,410,'两车组人数 2 ≤ 各自 b；总费用 2×1+1×2=4',size=23)
    save('P15232',f,'原样例车辆一只能单独走一条车道；将允许双车的第二、三辆放便宜车道，费用四。')

    f=Figure('最小值四的完整跨度是第3至5项，得分六十',390)
    f.row([3,1,6,4,5,2],100,x=35,width=115,colors={0:GRAY,1:RED,2:GREEN,3:GREEN,4:GREEN,5:RED})
    f.text(45,245,'跨度 [6,4,5]：元素和 15，最小值 4',GREEN,size=24)
    f.text(45,310,'左右的 1、2 都更小，不能再按最小值 4 扩展',size=23)
    f.text(45,365,'15×4=60；同分按更短、再更靠左取',size=23)
    save('UVA1619',f,'原样例最优端点三、五；边界值一与二严格小于四，将该最大可扩展跨度限制在中间三项。')

    f=Figure('二乘二全空白纸，一共九个长方形',455)
    for i in range(2):
        for j in range(2):f.box(55+95*j,105+95*i,90,90,'.',GREEN,size=28)
    f.text(315,150,'底在第一行：高度 [1,1]',size=22);f.text(315,205,'后缀贡献 1、2，共 3',GREEN,size=23)
    f.text(315,285,'底在第二行：高度 [2,2]',size=22);f.text(315,340,'后缀贡献 2、4，共 6',GREEN,size=23)
    f.text(45,420,'总计 3+6=9，也等于四单格、四双格、一个整格',size=22)
    save('P1950',f,'实际二乘二空白网格，把矩形按底行与右列划分后，每个高度选择只计一次。')

    f=Figure('坐标五至八包含三色，彩带长度是三',455)
    f.parts.append('<rect x="430" y="80" width="210" height="265" rx="8" fill="#12805c" fill-opacity="0.10"/>')
    for color,y,positions,label in [(RED,140,[5],'颜色1'),(BLUE,225,[1,7],'颜色2'),(GREEN,310,[1,3,8],'颜色3')]:
        f.text(30,y+7,label,color,size=20)
        for p in positions:f.circle(80+70*p,y,p,color,radius=24)
    f.line(80,370,710,370,GRAY)
    for p in range(10):f.text(80+70*p,400,p,GRAY,size=19,anchor='middle')
    f.text(45,445,'原样例：选到位置 5、7、8；8−5=3，不加一',size=22)
    save('P2564',f,'坐标一的两色珠子分行展示，没有错误合并；绿色竖带只覆盖五至八这一可行范围。')

    f=Figure('序列 [1,2,3] 的六个非空连续区间，极差和四',445)
    f.row([1,2,3],95,x=135,width=160)
    f.text(45,230,'三段单项：极差都是 0',size=24)
    f.text(45,300,'两段双项：[1,2] 与 [2,3]，各为 1',size=24)
    f.text(45,370,'一段三项：[1,2,3]，极差为 2',size=24)
    f.text(45,425,'总和 0+0+0+1+1+2=4',GREEN,size=24)
    save('P6503',f,'原第一组样例逐个区间核对，单项区间也存在，只是最大与最小相同、贡献零。')

    f=Figure('最小值恰一百：至少一百的五个，减至少一百零一的两个',450)
    for i,row in enumerate([[100,101],[101,99]]):
        for j,value in enumerate(row):f.box(55+110*j,105+110*i,105,100,value,GREEN if value==100 else RED if value==99 else BLUE,size=26)
    f.text(340,165,'全 ≥100：5 个矩形',GREEN,size=23);f.text(340,255,'全 ≥101：2 个矩形',BLUE,size=23);f.text(340,345,'恰等于100：5−2=3',GREEN,size=23)
    f.text(45,420,'三者是左上单格、第一行、第一列，均不含右下99',size=21)
    save('P7410',f,'这个实际二乘二示例含一个低于阈值的障碍，补集差准确留下至少含一个一百的三个矩形。')

    f=Figure('M=5、K=2：四座三层塔，加一座两层塔，共14只',470)
    for j in range(5):
        levels=[9,7,5] if j<4 else [7,5]
        for i,w in enumerate(levels):f.box(45+140*j,325-80*i,120,65,w,GREEN)
    f.text(45,435,'原样例：9用4只、7用5只、5用5只，另1只7不放',size=22)
    save('P9977',f,'每座塔直接相邻重量差都为二；用四只九承载四座三层，另有一座七、五组成的两层塔。')

    f=Figure('反向追到初场结束时刻3与1，对应可能农夫1与2',475)
    for x,y,label,color in [(150,185,'1',GREEN),(360,185,'3',GREEN),(620,105,'8',GREEN),(620,285,'9',GRAY),(360,370,'4159',GRAY)]:f.circle(x,y,label,color,radius=34 if label=='4159' else 28)
    f.line(180,185,330,185,GREEN);f.text(250,155,'1→3',GREEN,size=23,anchor='middle')
    f.line(385,175,595,115,GREEN);f.text(490,100,'3→8',GREEN,size=23,anchor='middle')
    f.line(385,195,595,275,GRAY);f.text(500,265,'3→9',GRAY,size=23,anchor='middle')
    f.text(60,265,'农夫2初场结束1',size=21);f.text(250,300,'农夫1初场结束3',size=21)
    f.text(45,450,'原样例 T=8；初场结束 3、1、4159，输出 110',size=23)
    save('P10277',f,'实边按面试开始到结束标明方向；从八反向可达三与一，第三位农夫的初场结束4159不可达。')

    f=Figure('跨度内的最小值三，可以为短于它的窗口提供候选',435)
    f.row([1,2,3,4,3],95,x=55,width=130,colors={2:GREEN,3:GREEN,4:GREEN})
    f.text(45,225,'第3至5项最小为3，跨度长3，可提供长度1、2、3',size=21)
    f.row([4,3,3,2,1],290,x=55,width=130,colors={i:GREEN for i in range(5)})
    f.text(45,405,'全部最优强度：4、3、3、2、1；长跨度向短传播',size=22)
    save('CF547B',f,'实际五项示例的每个长度答案，长度一的最优四来自更高的单项，不会被传播来的三压低。')

    f=Figure('原第二样例从第4首开始：听六次，第七次触发停止',450)
    f.row([3,3,2,5,3,3,2],100,x=45,width=95,colors={i:GREEN if i<6 else RED for i in range(7)})
    f.text(45,230,'已听最大值依次：3、3、3、5、5、5',size=23)
    f.text(45,300,'第二次听到2时，2×2 < 5，立即停，它不计入',RED,size=23)
    f.text(45,370,'同一首重复播放要逐次计数；答案为 6',size=23)
    f.text(45,425,'新值等于一半时不满足严格小于，继续听',size=22)
    save('CF1237D',f,'循环实际展开为三三二五三三二，第一次二在遇到五之前可以听，最后这个二才触发停止。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n';spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
