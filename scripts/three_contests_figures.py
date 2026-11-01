"""Draw the actual objects used by the November round explanations."""
from html import escape
from pathlib import Path
import datetime as dt
import shutil
from three_contests_programs import CONTENT, ARCHIVE, ROUNDS

class Figure:
    def __init__(self,title,width=920,height=330):
        self.width,self.height=width,height
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
          '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="none" stroke="#476782" stroke-width="1.5"/></marker></defs>',
          f'<rect width="{width}" height="{height}" rx="12" fill="#f8fbff"/>',
          '<g font-family="Microsoft YaHei,Arial,sans-serif" font-size="19" fill="#1c324a">']
        self.text(24,34,title,22)
    def text(self,x,y,s,size=18,anchor='start',color='#1c324a'):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{escape(str(s))}</text>')
    def box(self,x,y,w,h,label,fill='#e7f1fa'):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#6b89a4"/>')
        self.text(x+w/2,y+h/2+7,label,18,'middle')
    def line(self,x1,y1,x2,y2,arrow=False,color='#476782',dash=False):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.4"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="6 5"' if dash else '')+'/>')
    def circle(self,x,y,label,fill='#d9edf9',radius=23):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="#476782" stroke-width="2"/>')
        self.text(x,y+6,label,17,'middle')
    def save(self,key,name):
        text=''.join(self.parts)+'</g></svg>\n'
        platform,series,number,_,_=ROUNDS[key]
        for folder in [CONTENT/key/'assets',ARCHIVE/platform/series/number/'assets']:
            folder.mkdir(parents=True,exist_ok=True)
            path=folder/name
            if path.exists() and path.read_text('utf8')!=text:
                saved=Path.home()/'.dsh/backups/three-contests-20261102'/dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')/key/name
                saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,saved)
            path.write_text(text,encoding='utf8')

def make():
    f=Figure('外圈是四条边的并集；角只属于一个被统计的格子',920,280)
    for i in range(3):
        for j in range(4):
            f.box(40+j*67,70+i*55,57,45,'#' if (i,j) in [(0,0),(0,3),(1,1),(1,2),(2,0),(2,1)] else '.', '#d4eddf' if i in [0,2] or j in [0,3] else '#e8edf2')
    f.text(365,105,'绿色格：最外圈；中间两格不计入')
    f.text(365,151,'一个格子只判断一次，因此四个角不重复')
    f.text(365,205,'单行 / 单列时，整行 / 整列都是外圈')
    f.save('week168','border.svg')

    f=Figure('两个和都包含当前位置 i；先求后缀，再更新前缀',920,270)
    for j,value in enumerate([2,-1,5,3,4]):f.box(130+j*120,80,100,52,str(value),'#ffedc5' if j==2 else '#e7f1fa')
    f.text(420,66,'i = 3',18,'middle')
    f.line(135,167,470,167);f.text(300,194,'前缀 P = 2 − 1 + 5 = 6',18,'middle')
    f.line(375,221,710,221);f.text(550,248,'后缀 S = 5 + 3 + 4 = 12',18,'middle')
    f.text(755,103,'总和 13',18);f.text(755,135,'旧前缀 1',18)
    f.save('week168','prefix-suffix.svg')

    f=Figure('原圈走 d 步 → 查询空格 → 占用后把查询链接接到后继',920,310)
    for i in range(1,7):f.box(30+(i-1)*115,78,90,52,str(i),'#e8edf2' if i in [1,2,6] else '#d4eddf')
    f.text(40,164,'灰色：已占用 1、2、6；绿色：空格 3、4、5')
    f.line(715,104,830,104,True);f.text(772,80,'哨兵 7',17,'middle')
    f.line(65,209,305,209,True);f.text(185,196,'find(1) = 3',18,'middle')
    f.line(650,245,825,245,True);f.text(737,231,'find(6) = 7',18,'middle')
    f.text(40,281,'到哨兵后再 find(1)，得到空格 3；原始步数仍按 n = 6 计算')
    f.save('week168','successor.svg')

    f=Figure('取物顺序 A₁ → B₁ → A₂ → A₃，恰好四件，总价值 17',920,290)
    data=[('A₁：8 / 标记1','(1,0,A)'),('B₁：5 / 标记1','(1,1,B)'),('A₂：−3 / 标记0','(2,1,A)'),('A₃：7 / 标记1','(3,1,A)')]
    for i,(top,bottom) in enumerate(data):
        x=25+i*225;f.box(x,84,195,65,top,'#d4eddf' if i in [0,2,3] else '#ffedc5');f.text(x+98,181,bottom,18,'middle')
        if i<3:f.line(x+199,115,x+221,115,True)
    f.text(35,225,'A₁ 的标记1：先换到 B。A₂ 的标记0：可以继续取 A₃。')
    f.text(35,264,'最后的 A₃ 即使标记为1，也不要求再取第五件。')
    f.save('week168','stack-path.svg')

    f=Figure('被标记为“已保证不喝奶”的配对，不能重复朋友或菜',920,340)
    for j in range(3):f.text(280+j*80,80,f'菜 {j+1}',17,'middle')
    for i,a in enumerate([1,1,3]):
        f.text(45,125+i*62,f'朋友 {i+1}：a = {a}',18)
        for j in range(3):f.box(245+j*80,95+i*62,68,46,'可选' if j<a else '超辣','#d4eddf' if j<a else '#f5e1df')
    f.text(535,113,'按 a 从小到大处理')
    f.text(535,163,'之前已选 j−1 道菜，全部 ≤ 当前 a')
    f.text(535,213,'当前朋友可选 a−(j−1) 道安全菜')
    f.text(45,307,'示例 a = (1,1,3)：R₁ = 5，R₂ = 4，R₃ = 0，答案 2×5 − 2×4 = 2')
    f.save('week168','rook.svg')

    f=Figure('前缀内的标记1必须用另一堆隔开；标记0可以额外切段',920,330)
    f.text(30,83,'A 前三件：');f.box(180,55,160,55,'8 / 标记1','#d4eddf');f.box(380,55,160,55,'−3 / 标记0','#d4eddf');f.box(550,55,160,55,'7 / 标记1','#d4eddf')
    f.line(359,53,359,115,color='#c14e48',dash=True)
    f.text(30,160,'最少两段：');f.box(180,130,160,52,'[ A₁ ]','#d4eddf');f.box(380,130,330,52,'[ A₂, A₃ ]','#d4eddf')
    f.text(30,235,'插入 B₁：');f.box(180,205,160,52,'[ A₁ ]','#d4eddf');f.box(380,205,130,52,'[ B₁ ]','#ffedc5');f.box(550,205,330,52,'[ A₂, A₃ ]','#d4eddf')
    f.text(30,302,'A 内部一次强制切段 ≤ B 的一件；若 B 一件也不取，就无法隔开。')
    f.save('week168','stack-blocks.svg')

    f=Figure('每条 Bingo 线的代价，就是这条线内尚未标记的格数',920,310)
    for i in range(5):
        for j in range(5):f.box(40+j*44,65+i*42,38,36,'o' if j==i and i!=2 else '.', '#d4eddf' if j==i else '#e7f1fa')
    f.text(340,106,'五行 + 五列 + 两条对角线，共十二条候选线')
    f.text(340,161,'图中主对角线仅缺中央一格，补一个即可')
    f.text(340,218,'枚举每条线并取最小值；已有完整线时为零')
    f.save('abc482','bingo.svg')

    f=Figure('排序后的坐标保留重复值；闭区间 [2,4] 对应一段下标',920,300)
    vals=[1,2,2,4,5]
    for i,v in enumerate(vals):f.box(110+i*125,84,95,52,str(v),'#d4eddf' if 1<=i<4 else '#e7f1fa');f.text(157+i*125,161,f'下标 {i}',16,'middle')
    f.line(220,207,600,207,True);f.text(415,241,'保留三个位置：2、2、4',18,'middle')
    f.text(80,279,'lower_bound(2) = 1；upper_bound(4) = 4；数量 = 4 − 1 = 3')
    f.save('abc482','bounds.svg')

    f=Figure('k = 2：先与右邻居相遇，再由两位传播者分别到达两端',920,430)
    f.text(30,72,'初始坐标：2、4（初始感染）、10、14、18。取右侧邻居 10。',18)
    x=lambda v:100+v*29
    y=lambda t:115+t*31
    f.line(x(0),y(0),x(20),y(0),True)
    f.line(x(0),y(0),x(0),y(8),True)
    f.text(40,365,'时间',16);f.text(710,113,'坐标',16)
    for v in [2,4,10,18]:f.text(x(v),y(0)-13,str(v),17,'middle')
    f.line(x(2),y(0),x(6),y(4),color='#368b66')
    f.line(x(4),y(0),x(11),y(7),color='#b76a30')
    f.line(x(10),y(0),x(6),y(4),color='#b76a30')
    f.line(x(18),y(0),x(11),y(7),color='#368b66')
    for v,t,label in [(7,3,'首次接触：t=3'),(6,4,'左端接触：t=4'),(11,7,'右端接触：t=7')]:
        f.circle(x(v),y(t),'',radius=5,fill='#b76a30');f.text(x(v)+17,y(t)+5,label,17)
    f.text(30,407,'橙线：两位传播者的轨迹。绿色：两端的人相向移动。完成时间 max(4,7) = 7。',18)
    f.save('abc482','zombie.svg')

    f=Figure('偶数直径共用一个中心；奇数直径共用一条中心边',920,380)
    f.text(190,74,'D = 4，半径 2',20,'middle')
    even=[(200,185,'中心'),(100,135,''),(300,135,''),(200,280,''),(45,85,'红'),(355,85,'红'),(200,335,'蓝')]
    for a,b in [(0,1),(0,2),(0,3),(1,4),(2,5),(3,6)]:f.line(even[a][0],even[a][1],even[b][0],even[b][1])
    for x,y,l in even:f.circle(x,y,l,'#ffedc5' if l=='中心' else '#f4d8d5' if l=='红' else '#d9edf9',19)
    f.text(475,74,'D = 3，两侧各走 1 条边',20)
    coords=[(590,200,'左心'),(740,200,'右心'),(510,115,'红'),(510,285,'蓝'),(820,115,'红'),(820,285,'红')]
    for a,b in [(0,1),(0,2),(0,3),(1,4),(1,5)]:f.line(coords[a][0],coords[a][1],coords[b][0],coords[b][1],color='#b76a30' if (a,b)==(0,1) else '#476782')
    for x,y,l in coords:f.circle(x,y,l,'#ffedc5' if '心' in l else '#f4d8d5' if l=='红' else '#d9edf9',21)
    f.text(45,365,'同色端点必须来自不同中心分支。',17)
    f.text(475,365,'红色端点：左侧一个 × 右侧两个 = 两对。',17)
    f.save('abc482','diameter.svg')

    f=Figure('N = 6 = 2×3：一轮分成两层，开始一轮时才增加代价',920,360)
    nodes=[(30,95,'层0 / 余1'),(335,95,'层1 / 余2'),(640,95,'层0 / 余6')]
    for x,y,l in nodes:f.box(x,y,230,58,l,'#d4eddf' if '层0' in l else '#ffedc5')
    f.line(266,124,329,124,True);f.line(571,124,634,124,True)
    f.text(295,79,'×2，花费1',17,'middle');f.text(600,79,'×3，花费0',17,'middle')
    f.text(30,204,'一轮得到约数 2×3=6；也可在任一层选指数0，即乘1。')
    f.box(30,242,190,50,'余1 / t=0');f.box(345,242,190,50,'余2 / t=1');f.box(660,242,190,50,'余4 / t=2')
    f.line(227,268,338,268,True);f.line(542,268,653,268,True)
    f.text(285,233,'一轮乘2',17,'middle');f.text(600,233,'再一轮乘2',17,'middle')
    f.text(30,337,'模 7 时余4最少需要两轮。终点只读取回到层0的完整轮次；余1答案为1。')
    f.save('abc482','layers.svg')
    print('Created 11 figures in portable content and authoring archive.')

if __name__=='__main__':make()
