// Navigation metadata describes a whole list, never a problem's rating or mastery.
// Keep the original title, source URL, roster and chapter order as their identity.
export const CATEGORY_ORDER = ['语言入门', '基础算法', '搜索', '动态规划', '数据结构', '图论', '字符串', '数学', '计算几何', '进阶技巧', '赛事真题', '教材配套', '综合训练', '待补充信息'];
const TOPIC_ORDER = {
  '字符串': ['字符串基础', '模式匹配', '字典树', '字符串哈希', '后缀结构', '回文算法', '后缀与回文综合', '综合练习'],
  '动态规划': ['入门', '线性动态规划', '背包', '区间动态规划', '树形动态规划', '状态压缩', '数位动态规划', '动态规划优化', '综合练习'],
  '基础算法': ['模拟与枚举', '排序', '前缀和与差分', '二分与三分', '双指针', '递推与分治', '贪心与构造', '位运算', '表达式解析', '综合练习'],
  '数据结构': ['线性表与容器', '堆与二叉树', '并查集', '堆与树状数组', '树状数组', '线段树', '单调栈与单调队列', '分块与莫队', '平衡树与动态树', '空间数据结构', '其他结构', '综合练习'],
  '图论': ['最短路', '生成树', '树上算法', '树链剖分', '连通性', '拓扑排序与 2-SAT', '网络流与匹配', '综合练习'],
  '数学': ['数论', '组合与计数', '概率与期望', '线性代数', '数论与线性代数', '多项式与生成函数', '博弈', '数值计算', '综合练习'],
  '综合训练': ['基础综合', '思维训练', '算法模板', '进阶综合', '精选习题', '作者题集', '趣味与主题题集'],
};

const TOPICS = [
  ['字符串', '模式匹配', /KMP|ACAM|AC\s*自动机|模式匹配|Z\s*函数/i],
  ['字符串', '后缀与回文综合', /后缀.*回文|回文.*后缀/i],
  ['字符串', '后缀结构', /后缀|\bSAM\b|StringSuffix/i],
  ['字符串', '回文算法', /回文|manacher|eertree/i],
  ['字符串', '字典树', /字典树|\btrie\b/i],
  ['字符串', '字符串哈希', /字符串.*哈希|散列|哈希|\bhash\b/i],
  ['字符串', '字符串基础', /入门5|基础字符串/],
  ['字符串', '综合练习', /字符串/],
  ['动态规划', '数位动态规划', /数位\s*(?:DP|动态规划)/i],
  ['动态规划', '背包', /背包|knapsack/i],
  ['动态规划', '树形动态规划', /树.{0,5}(?:DP|动态规划)|(?:DP|动态规划).{0,5}树/i],
  ['动态规划', '区间动态规划', /区间.{0,5}(?:DP|动态规划)|环形动态规划/i],
  ['动态规划', '状态压缩', /状压|状态压缩|轮廓线/i],
  ['动态规划', '动态规划优化', /(?:DP|动态规划).{0,5}优化|斜率优化|决策单调|Slope\s*Trick|wqs|插值优化/i],
  ['动态规划', '线性动态规划', /线性状态|线性动态规划/],
  ['动态规划', '入门', /新手动态规划|小白.*DP|动态规划的引入/i],
  ['动态规划', '综合练习', /动态规划|\bDP\b/i],
  ['图论', '树链剖分', /树链|树剖|重链剖分/],
  ['图论', '树上算法', /树上|点分治|点分树|虚树|LCA|最近公共祖先|树形结构|\btrees\b/i],
  ['图论', '连通性', /连通|联通|割点|割边|缩点|圆方树|Tarjan/i],
  ['图论', '生成树', /生成树|重构树/],
  ['图论', '最短路', /最短路|最[（(]次[）)]短路|次短路|差分约束|SPFA|分层图/i],
  ['图论', '网络流与匹配', /网络流|网络瘤|费用流|最大流|最小割|二分图|匹配/],
  ['图论', '拓扑排序与 2-SAT', /拓扑|2[ -]?SAT/i],
  ['图论', '树上算法', /【图论2-1】树|图论树论/],
  ['图论', '综合练习', /图论|图的基本|\bgraphs\b/i],
  ['数据结构', '线段树', /线段树|主席树|Li\s*Chao/i],
  ['数据结构', '堆与树状数组', /二叉堆与树状数组/],
  ['数据结构', '树状数组', /树状数组/],
  ['数据结构', '并查集', /并查集/],
  ['数据结构', '平衡树与动态树', /平衡树|动态树|Splay|Treap|ETT/i],
  ['数据结构', '空间数据结构', /K[ -]?D[ -]?Tree/i],
  ['数据结构', '分块与莫队', /分块|莫队|sqrt\s*technology|根号数据结构/i],
  ['数据结构', '单调栈与单调队列', /单调栈|单调队列/],
  ['数据结构', '线性表与容器', /线性表|链表|集合|\bSTL\b/i],
  ['数据结构', '堆与二叉树', /二叉树|二叉堆|优先队列/],
  ['数据结构', '其他结构', /珂朵莉树|析合树/],
  ['数据结构', '综合练习', /数据结构|\bDS\b/i],
  ['数学', '概率与期望', /概率|期望|统计/],
  ['数学', '数论与线性代数', /数论和线性代数/],
  ['数学', '多项式与生成函数', /多项式|生成函数|FFT|NTT|OGF|EGF|拉格朗日/i],
  ['数学', '线性代数', /线性代数|高斯|矩阵|线性基/i],
  ['数学', '组合与计数', /组合|计数|容斥|卡特兰|群论|置换群|Polya/i],
  ['数学', '数论', /数论|同余|素数|质数|莫比乌斯|欧拉|整除|筛法|BSGS|Exgcd|逆元|CRT|最大公约数|最小公倍数/i],
  ['数学', '博弈', /博弈/],
  ['数学', '数值计算', /数值算法/],
  ['计算几何', '综合练习', /几何|凸包/],
  ['数学', '综合练习', /数学/],
  ['搜索', '双向搜索', /双向搜索/],
  ['搜索', '启发式搜索', /IDA\*|A\*|迭代加深/],
  ['搜索', '精确覆盖', /舞蹈链|\bDLX\b/i],
  ['搜索', '综合练习', /搜索|\bBFS\b|\bDFS\b|剪枝/i],
  ['基础算法', '前缀和与差分', /前缀和|差分|离散化/],
  ['基础算法', '二分与三分', /二分|三分/],
  ['基础算法', '贪心与构造', /贪心|构造/],
  ['基础算法', '排序', /排序/],
  ['基础算法', '双指针', /双指针|尺取|滑动窗口/],
  ['基础算法', '模拟与枚举', /模拟|枚举|高精度/],
  ['基础算法', '递推与分治', /递推|递归|分治|倍增/],
  ['基础算法', '位运算', /位运算/],
  ['基础算法', '综合练习', /基本算法|基础算法/],
  ['语言入门', '基础语法', /入门[1-6]|顺序结构|分支结构|循环结构|数组|语言入门|函数与结构体/],
];

const OVERRIDES = {
  'luogu-100': ['顺序结构 · 入门', '语言入门/基础语法'],
  'luogu-101': ['分支结构 · 入门', '语言入门/基础语法'],
  'luogu-102': ['循环结构 · 入门', '语言入门/基础语法'],
  'luogu-103': ['数组 · 入门', '语言入门/基础语法'],
  'luogu-105': ['函数与结构体 · 入门', '语言入门/基础语法'],
  'luogu-207': ['树的基础与应用 · 专项练习', '图论/树上算法'],
  'luogu-104': ['字符串基础 · 入门', '字符串/字符串基础'],
  'luogu-203': ['字符串算法 · 进阶综合', '字符串/综合练习'],
  'luogu-7768': ['KMP 与 AC 自动机 · 基础练习', '字符串/模式匹配'],
  'luogu-53971': ['字符串 · 综合练习', '字符串/综合练习'],
  'luogu-5061': ['字典树（Trie）· 基础练习', '字符串/字典树'],
  'luogu-3202': ['后缀结构 · 综合练习', '字符串/后缀结构'],
  'luogu-60465': ['AC 自动机 · 专项练习', '字符串/模式匹配'],
  'luogu-6625': ['字符串哈希 · 入门', '字符串/字符串哈希'],
  'luogu-379836': ['字符串哈希 · 综合练习', '字符串/字符串哈希'],
  'luogu-4790': ['后缀数组 · 专项练习', '字符串/后缀结构'],
  'luogu-5322': ['后缀自动机（SAM）· 专项练习', '字符串/后缀结构'],
  'luogu-169932': ['后缀数组、后缀自动机与回文自动机', '字符串/后缀与回文综合'],
  'luogu-22566': ['回文自动机 · 专项练习', '字符串/回文算法'],
  'luogu-4814': ['后缀结构 · 第 1 组', '字符串/后缀结构'],
  'luogu-11849': ['数列分块与整除分块 · 入门', '进阶技巧/综合专题'],
  'luogu-1125': ['线段树与树链剖分 · 综合应用', '图论/树链剖分'],
  'luogu-9583': ['悬线法 · 专项练习', '动态规划/动态规划优化'],
  'luogu-15766': ['基本算法与数据结构 · 第 1、2 章', '教材配套/算法竞赛进阶指南'],
  'luogu-3135': ['数学题 · 实现训练', '数学/综合练习'],
  'luogu-3504': ['趣味与非常规题目 · 精选', '综合训练/趣味与主题题集'],
  'luogu-3210': ['复杂模拟与实现 · 综合练习', '基础算法/模拟与枚举'],
  'luogu-1138': ['基础题 · 综合练习', '综合训练/基础综合'],
  'luogu-2390': ['动态规划 · 基础练习', '动态规划/入门'],
  'luogu-470544': ['特色题目 · 精选', '综合训练/精选习题'],
  'luogu-1015434': ['解题技巧 · 综合练习', '进阶技巧/综合专题'],
  'luogu-542418': ['思维与观察 · 基础练习', '综合训练/思维训练'],
  'luogu-322838': ['小 E 题 · 精选', '综合训练/精选习题'],
  'luogu-5644': ['代码解析与求值 · 专项练习', '基础算法/表达式解析'],
  'luogu-5642': ['表达式解析与求值 · 专项练习', '基础算法/表达式解析'],
  'luogu-4066': ['程序常数与性能优化 · 专项练习', '进阶技巧/实现与优化'],
  'luogu-201': ['常见优化技巧 · 综合练习', '进阶技巧/实现与优化'],
  'luogu-269907': ['珂朵莉树 · 基础练习', '数据结构/其他结构'],
  'luogu-9391': ['算法综合 · 能力提升', '综合训练/精选习题'],
  'luogu-743042': ['蓝桥杯省赛 · 专项训练', '赛事真题/蓝桥杯'],
  'luogu-759988': ['蓝桥杯国赛 · 专项训练', '赛事真题/蓝桥杯'],
  'luogu-1367': ['退役 OIer 选编 · 综合练习', '综合训练/精选习题'],
  'luogu-584445': ['resot 选编 · 综合练习', '综合训练/精选习题'],
  'luogu-571221': ['KTT 选编 · 综合练习', '综合训练/精选习题'],
  'luogu-12927': ['动态规划 · 提高练习', '动态规划/综合练习'],
  'luogu-1323': ['动态规划 · 提高练习', '动态规划/综合练习'],
  'luogu-14206': ['图论 · 综合练习', '图论/综合练习'],
  'luogu-5297': ['数据结构维护技巧 · 综合练习', '数据结构/综合练习'],
  'luogu-11363': ['树形动态规划 · 专项练习', '动态规划/树形动态规划'],
  'luogu-8793': ['反悔贪心 · 专项练习', '基础算法/贪心与构造'],
  'luogu-1008': ['多项式 · 第 1 组', '数学/多项式与生成函数'],
  'luogu-200296': ['数论推导 · 专项练习', '数学/数论'],
  'luogu-2957': ['数据结构 · 普及练习', '数据结构/综合练习'],
  'luogu-4986': ['图论与树上算法 · Div.3 练习', '图论/综合练习'],
  'luogu-201862': ['动态规划 · 中级综合', '动态规划/综合练习'],
  'luogu-147101': ['网络流 · 综合练习', '图论/网络流与匹配'],
  'luogu-8353': ['数据结构 · 第 1 组', '数据结构/综合练习'],
  'luogu-235774': ['数据结构精选 · 第 2 组', '数据结构/综合练习'],
  'luogu-4953': ['数据结构 · 经典练习', '数据结构/综合练习'],
  'luogu-4837': ['最短路与次短路 · 专项练习', '图论/最短路'],
  'luogu-288387': ['精选习题 · 第 1 组', '综合训练/精选习题'],
  'luogu-370967': ['精选习题 · 第 2 组', '综合训练/精选习题'],
  'luogu-404828': ['精选习题 · 第 3 组', '综合训练/精选习题'],
  'luogu-425024': ['精选习题 · 第 4 组', '综合训练/精选习题'],
  'luogu-466134': ['精选习题 · 第 5 组', '综合训练/精选习题'],
  'luogu-4840': ['树形动态规划 · 专项练习', '动态规划/树形动态规划'],
  'luogu-1344': ['算法模板 · 省选', '综合训练/算法模板'],
  'luogu-813583': ['Google Code Jam · 配套练习', '教材配套/挑战程序设计竞赛'],
  'luogu-7764': ['EternalAlexander · 原创题集', '综合训练/作者题集'],
  'luogu-3503': ['Elegia · 公开题集', '综合训练/作者题集'],
  'luogu-65436': ['小琢 · 原创题集', '综合训练/作者题集'],
  'luogu-55555': ['w33z8kqrqk8zzzx33 · 原创题集', '综合训练/作者题集'],
  'luogu-444558': ['NaCly_Fish · 原创题集', '综合训练/作者题集'],
  'luogu-2017': ['Feecle6418 · 原创题集', '综合训练/作者题集'],
};

const clean = value => String(value || '').normalize('NFKC').replace(/[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]/g, '').replace(/\s+/g, ' ').trim();
const chineseNumber = value => ({一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9, 十: 10}[value] || value);

function bookName(list) {
  const category = (list.categories || []).find(item => item.id.startsWith('book.'));
  if (category) return ({'book.yibentong1': '信息学奥赛一本通', 'book.shizhanbiji': '算法竞赛实战笔记'}[category.id] || category.name.replace(/[《》]/g, ''));
  const title = clean(list.title);
  if (/算法竞赛.*训练指南/.test(title)) return '算法竞赛入门经典训练指南';
  if (/算法竞赛入门经典/.test(title)) return '算法竞赛入门经典';
  if (/算法竞赛进阶指南/.test(title)) return '算法竞赛进阶指南';
  if (/挑战程序设计竞赛/.test(title)) return '挑战程序设计竞赛';
  return '';
}

export function categoryPath(title) {
  const text = clean(title);
  if (/模拟退火|随机化/.test(text)) return ['进阶技巧', '随机化与模拟退火'];
  if (/交互/.test(text)) return ['进阶技巧', '交互题'];
  if (/根号分治/.test(text)) return ['基础算法', '递推与分治'];
  const topic = TOPICS.find(([, , pattern]) => pattern.test(text));
  if (topic) return topic.slice(0, 2);
  if (/GESP/i.test(text)) return ['赛事真题', 'GESP'];
  if (/蓝桥杯/.test(text)) return ['赛事真题', '蓝桥杯'];
  if (/CSP|NOIP/i.test(text)) return ['赛事真题', 'CSP 与 NOIP'];
  if (/USACO/i.test(text)) return ['赛事真题', 'USACO'];
  if (/国家集训队|APIO|WC\s*20/i.test(text)) return ['赛事真题', '集训与讲课'];
  if (/月赛|年度试题推荐/.test(text)) return ['赛事真题', '洛谷月赛'];
  if (/传智杯/.test(text)) return ['赛事真题', '传智杯'];
  if (/Codeforces|\bCF\b|AtCoder|NERC|NEERC/i.test(text)) return ['赛事真题', '其他公开赛'];
  if (/Ynoi/i.test(text)) return ['赛事真题', 'Ynoi'];
  if (/OI\b|OI[」 】]|Rounds?|CGR|HBTSC|LACPT|ALFR|EZEC|公开赛|系列试题|历届比赛/i.test(text)) return ['赛事真题', '其他公开赛'];
  if (/思维|Ad.hoc|脑筋/i.test(text)) return ['综合训练', '思维训练'];
  if (/模板|板子库/.test(text)) return ['综合训练', '算法模板'];
  if (/Project|古风|LoveLive|BanGDream|末日时|主题题单/i.test(text)) return ['综合训练', '趣味与主题题集'];
  if (/出的题|原创题|公开题|的题目|の题|的题$/.test(text)) return ['综合训练', '作者题集'];
  if (/普及|基础|新手|入门/.test(text)) return ['综合训练', '基础综合'];
  if (/提高|省选|S 组|蓝题/.test(text)) return ['综合训练', '进阶综合'];
  return ['综合训练'];
}

function normalizedTitle(list, path) {
  const original = clean(list.title);
  if (/^洛谷题单 \d+$/.test(original)) return `关联题单 · ${original.match(/\d+/)[0]}`;
  const chapter = original.match(/(?:第([一二三四五六七八九十\d]+)章|题单\s*([一二三四五六七八九十]+))/);
  const book = bookName(list);
  if (book && chapter && !TOPICS.some(([, , re]) => re.test(original.replace(/《[^》]+》/g, '')))) {
    const unit = original.includes('章') ? '章' : '组';
    const detail = /例题\s*\+\s*习题/.test(original) ? '例题与习题' : /习题/.test(original) ? '习题' : /例题/.test(original) ? '例题' : '配套练习';
    const part = original.match(/习题\s*[（(](\d+)[)）]/);
    return `第 ${chineseNumber(chapter[1] || chapter[2])} ${unit} · ${detail}${part ? `（${part[1]}）` : ''}`;
  }
  let text = original
    .replace(/[（(][^()（）]*《[^》]+》[^()（）]*[)）]/g, '')
    .replace(/\s*[-—]\s*[^《]*《[^》]+》/g, '')
    .replace(/《[^》]+》/g, '')
    .replace(/【(?:入门\d+|算法[\d-]+|数据结构[\d-]+|图论[\d-]+|动态规划\d+|数学[\d-]+)】/g, '')
    .replace(/[【\[][^\]】]*(?:日报|配套题单|要 有 前 缀|小峰)[^\]】]*[】\]]/g, '')
    .replace(/^[【\[](?:图论|字符串|数学|数论|线性代数|数据结构|动态规划|群论|搜索|网络瘤|ALG|DS)[】\]]\s*/i, '')
    .replace(/^[【\[（(](普及|提高|省选|普及\/DS|提高&省选)[】\]）)]\s*/, '$1 · ')
    .replace(/(?:从入门到入土|从入门到跳楼|从入门到精通)/g, '综合练习')
    .replace(/^『应用\(折磨\)篇』\s*/, '')
    .replace(/^(?:菜鸡|蒟蒻)\s*/, '')
    .replace(/^[A-Za-z0-9_]+\s*(?:的|の)\s*/, '')
    .replace(/^关于(?=SPFA)/i, '')
    .replace(/^\[模拟退火-优雅的暴力\]$/, '模拟退火 · 专项练习')
    .replace(/ACAM/gi, 'AC 自动机').replace(/AC自动机/g, 'AC 自动机')
    .replace(/\bcodeforces\b/gi, 'Codeforces').replace(/\bdp\b/gi, 'DP')
    .replace(/\bgraphs\b/gi, '图论').replace(/\btrees\b/gi, '树上算法').replace(/\bDS\b/g, '数据结构')
    .replace(/(?:题目)?题单|学习题单/g, '').replace(/(?:练习题小全|练习题目|练习题|试题推荐选集)/g, '练习')
    .replace(/经典好题|经典题目|经典题/g, '经典练习').replace(/好题/g, '精选习题')
    .replace(/\s*&\s*/g, '与').replace(/例题\s*\+\s*习题/g, '例题与习题').replace(/の/g, ' · ')
    .replace(/\s*Part\s+([IVX]+|\d+)/gi, ' · 第 $1 组')
    .replace(/([^\d])\s*#(\d+)/g, '$1 · 第 $2 组')
    .replace(/[!！~～]+$/g, '').replace(/^[\s:：·-]+|[\s:：·-]+$/g, '');
  text = clean(text).replace(/\s*[-—]\s*(例题|习题)/g, ' · $1');
  if (/^第一部分-/.test(text)) text = text.replace('-', ' · ');
  if (text === '字符串') text = '字符串 · 综合练习';
  if (text === '后缀数组') text = '后缀数组 · 专项练习';
  if (text === 'slope trick') text = 'Slope Trick · 动态规划优化';
  return text || path.at(-1) + ' · 配套练习';
}

export function describeTrainingList(list) {
  const override = OVERRIDES[list.id];
  let path = override?.[1].split('/') || categoryPath(list.title);
  const book = bookName(list);
  const chapterOnly = book && !TOPICS.some(([, , re]) => re.test(clean(list.title).replace(/《[^》]+》/g, '').replace(/算法竞赛(?:入门经典(?:[—-]*训练指南)?|进阶指南)/g, '')));
  if (book && (chapterOnly || path.length === 1 || /^第[一二三四五六七八九十\d]+部分/.test(clean(list.title)))) path = ['教材配套', book];
  if (/^洛谷题单 \d+$/.test(clean(list.title))) path = ['待补充信息', '关联题单'];
  else if (path.length === 1) path = [path[0], '精选习题'];
  const displayTitle = override?.[0] || normalizedTitle(list, path);
  let sourceLabel = book ? `《${book}》` : (list.categories || []).map(c => c.name).filter(x => x !== '精选用户分享').join(' · ');
  if (!sourceLabel) sourceLabel = '洛谷 ' + String(list.id).replace(/^luogu-/, '');
  return { ...list, displayTitle, topicPath: path, sourceLabel, originalTitle: list.title };
}

export function organizeTrainingLists(lists) {
  const organized = lists.map(describeTrainingList);
  const names = new Map();
  for (const list of organized) {
    const key = JSON.stringify([list.topicPath, list.displayTitle]);
    if (!names.has(key)) names.set(key, []);
    names.get(key).push(list);
  }
  // Equal subject names remain separate lists, with a stable source distinction.
  for (const group of names.values()) if (group.length > 1) {
    for (const list of group) list.sourceLabel += ` · ${list.id.replace(/^luogu-/, '')}`;
  }
  return organized;
}

const collator = new Intl.Collator('zh-CN', { numeric: true, sensitivity: 'base' });
function level(list) {
  const title = list.displayTitle;
  if (/入门|新手/.test(title)) return 0;
  if (/基础|普及|简单/.test(title) && !/不简单|省选|进阶|提高/.test(title)) return 1;
  if (/进阶|提高/.test(title)) return 3;
  if (/省选|高级/.test(title)) return 4;
  return 2;
}
export function compareTrainingLists(a, b) {
  return level(a) - level(b) || collator.compare(a.displayTitle, b.displayTitle) || collator.compare(a.id, b.id);
}
export function compareCategoryNames(a, b, parent = '') {
  const order = TOPIC_ORDER[parent] || CATEGORY_ORDER;
  const ai = order.indexOf(a), bi = order.indexOf(b);
  if (ai !== -1 && bi !== -1) return ai - bi;
  if (a === '综合练习') return b === a ? 0 : 1;
  if (b === '综合练习') return -1;
  return collator.compare(a, b);
}
