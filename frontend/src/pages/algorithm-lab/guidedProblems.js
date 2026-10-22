// Each prompt is an original paraphrase. Original statements/samples live in the public library.
export const GUIDED_PROBLEMS = [
  { pid: 'P1048', title: '采药', focus: '把时间看成容量', kind: 'pack',
    parts: ['有一段', ['总时间', '这是有限资源，对应背包容量。'], '，若干株草药各有', ['耗时和价值', '耗时消耗资源，价值是要最大化的收益。'], '。每株', ['最多采一次', '同一株不能反复采，容量倒序更新。'], '，求总价值最大。'],
    model: ['dp[c] 表示耗时不超过 c 时的最大总价值', 'dp[c] 表示已经采了 c 株草药', '总是先采价值最高的草药'],
    modelErrors: ['每株耗时不同，数量相同的组合也可能占用不同时间；需要记住的是时间上限。', '小例中第一株价值 7，但后两株合起来价值 8。先看组合是否更好。'],
    insight: '时间决定还装得下哪些草药；草药数量不必记进一维下标。',
    mini: { capacity: 5, items: [{ weight: 4, value: 7 }, { weight: 3, value: 5 }, { weight: 2, value: 3 }] },
    prediction: '这组小数据最多能得到多少价值？', answer: 8, reasoning: '后两株耗时 3+2=5，价值 5+3=8，比只采第一株的 7 更好。',
    state: 'dp[c]：已经处理过的草药中，耗时不超过 c 的最大总价值。当前草药耗时 t，价值 v。',
    line: 'dp[c] = max(dp[c], dp[c - t] + v);', source: '给当前草药留出 t 时间，读取未使用它的 dp[c-t]，再加它的价值。',
    initial: '所有 dp 初始为 0：没有草药时可什么都不采。', loop: '每株草药单独一轮，c 从 T 倒序到 t。', output: '输出 dp[T]。', complexity: '时间 O(MT)，空间 O(T)；T≤1000，M≤100。',
    bug: { title: '如果容量从小到大更新？', code: 'for (int c = t; c <= T; ++c)', input: 'T=4，只有一株：耗时 2、价值 3。', answer: 6, why: 'dp[2] 先变成 3，dp[4] 再读它，错误地把同一株采了两次；正确答案是 3。' },
    checks: ['只剩一株且总时间是它耗时的两倍，不能采两次', '耗时恰好等于总时间时要更新', '所有草药都超时，答案为 0'],
    recall: '题面不写“背包”时，你靠哪三个条件识别它？',
  },
  { pid: 'P1049', title: '装箱问题', focus: '把剩余最小改成已用最大', kind: 'space',
    parts: ['箱子体积上限为 V。每件物品有体积，', ['每件最多一次', '每件只处理一轮，仍然倒序。'], '，允许留下空隙。要求', ['剩余空间最小', 'V 固定，最小化 V−已装体积，等价于最大化已装体积。'], '。'],
    model: ['dp[c] 表示不超过 c 时最多能装多少体积', 'dp[c] 表示必须恰好装满 c', '没有给价值，所以不能用背包'],
    modelErrors: ['题目允许空隙，容量是上限，不要求每个中间状态都恰好装满。', '可以把已装体积本身当作要最大化的收益，最后再用 V 减去它。'],
    insight: '把物品体积同时当作重量和收益；求出最多装多少，再减一次。',
    mini: { capacity: 10, items: [{ weight: 6, value: 6 }, { weight: 3, value: 3 }, { weight: 2, value: 2 }] },
    prediction: '这组物品装完后，最少剩余多少空间？', answer: 1, reasoning: '最多装 6+3=9，剩余 10−9=1。不能把“最多装 9”直接当成输出。',
    state: 'dp[c]：容量不超过 c 时的最大已装体积。当前物品体积为 size。',
    line: 'dp[c] = max(dp[c], dp[c - size] + size);', source: '物品占 size，也给已装体积增加 size；来源仍是容量 c-size。',
    initial: '所有 dp 初始为 0：空箱是合法起点。', loop: '每件一轮，c 从 V 倒序到 size。', output: '输出 V - dp[V]。', complexity: '时间 O(nV)，空间 O(V)；V≤20000，n≤30。',
    bug: { title: '如果最后直接输出 dp[V]？', code: 'cout << dp[V];', input: 'V=10，物品体积为 6、3、2。', answer: 9, why: '程序会输出已装体积 9，题目要的是剩余空间 1。转移正确也可能在答案转换处出错。' },
    checks: ['可以恰好装满时输出 0', '所有物品都装不下时输出 V', '单件体积为 2、箱子为 4 时剩余 2'],
    recall: '另一道题要求“浪费最小”，什么时候能改写成“利用最大”？',
  },
  { pid: 'P1060', title: '开心的金明', focus: '先翻译题目的收益', kind: 'budget',
    parts: ['总预算有限，每件商品', ['只能买一次', '不是可以重复购买的完全背包。'], '。已知价格和重要度，要求', ['价格×重要度的总和最大', '重要度不是直接收益，价格也不只是收益：它同时是消耗。'], '，总花费不超过预算。'],
    model: ['消耗是价格，收益是价格×重要度', '消耗是重要度，收益是价格', '按重要度从高到低买'],
    modelErrors: ['限制的是花钱多少，所以容量消耗必须是价格；重要度参与计算题目定义的收益。', '把预算改成 6：价格 6、重要度 4 的收益为 24，优于价格 4、重要度 5 的 20。'],
    insight: '先用题目要最大化的表达式定义价值，再决定转移加什么。',
    mini: { capacity: 10, items: [{ weight: 6, importance: 4, value: 24 }, { weight: 4, importance: 5, value: 20 }, { weight: 5, importance: 3, value: 15 }] },
    prediction: '预算 10，表中三件商品的最大收益是多少？', answer: 44, reasoning: '买价格 6 和 4 的两件，收益是 6×4+4×5=44。重要度之和 9 不是本题目标。',
    state: 'dp[c]：花费不超过 c 的最大收益。当前价格 price，重要度 importance。',
    line: 'dp[c] = max(dp[c], dp[c - price] + price * importance);', source: '先扣价格得到剩余预算，再把题目定义的收益 price×importance 加回。',
    initial: '所有 dp 初始为 0：不购物花费 0，收益 0。', loop: '每件商品一轮，c 从总预算 N 倒序到 price。', output: '输出 dp[N]。', complexity: '时间 O(mN)，空间 O(N)；N<30000，m<25。',
    bug: { title: '如果转移只加重要度？', code: 'dp[c] = max(dp[c], dp[c-price] + importance);', input: '预算 10，商品为 (价格 6，重要度 4)、(4，5)。', answer: 9, why: '错误程序得到 4+5=9，正确目标是 6×4+4×5=44。用只有一两件商品的数据，就能检查收益有没有翻译对。' },
    checks: ['一件商品，预算刚好够：收益是价格×重要度', '价格高但买不起的商品不能贡献收益', '不要把价格与重要度读反，也不要求花光预算'],
    recall: '遇到新的“满意度”定义，你会先检查转移中的哪一项？',
  },
  { pid: 'P2392', title: '考前临时抱佛脚', focus: '从并行时间转成子集和', kind: 'balance',
    parts: ['四门课程要', ['逐科完成', '不同课程不能并行，最终把四科的最短用时相加。'], '。同一科的题可以分给两个大脑', ['同时计算', '这一科结束的时刻由工作量更多的大脑决定。'], '，每道题只能交给一边，求全部完成的最短时间。'],
    model: ['每科让较轻一边的耗时尽量接近总和的一半', '把所有课程一起分给两个大脑', '每次把下一题分给当前较空的一边，一定最优'],
    modelErrors: ['题目只允许同时处理同一科的题，不同课程必须分开计算，再把时间相加。', '耗时 8、7、6、5、4 时，这种贪心可能得到 17；分成 8+7 与 6+5+4，只需 15。'],
    insight: '一科总耗时 S 固定。若较轻一边耗时 x≤S/2，完成时间就是 S−x；所以让 x 尽量大。',
    mini: { capacity: 7, items: [{ weight: 1, value: 1 }, { weight: 2, value: 2 }, { weight: 3, value: 3 }, { weight: 8, value: 8 }] },
    prediction: '只看这一科，耗时 1、2、3、8，两个大脑最快多久完成？', answer: 8, reasoning: '总和 14。较轻一边最多做到 6，另一边是 8；完成时间为 max(6,8)=8。',
    state: '只看一科：S 为该科总耗时，H=floor(S/2)。dp[c] 是不超过 c 时能分到一边的最大耗时；当前题耗时 t。',
    line: 'dp[c] = max(dp[c], dp[c - t] + t);', source: '时间既是容量消耗，也是要尽量凑大的子集和。一道题只能分给一边，仍按 0/1 更新。',
    initial: '每开始新的一科，都重新把 dp 全部清零。', loop: '每科内部：每题一轮，c 从 H 倒序到 t。', output: '本科学习时间为 S - dp[H]，四科分别计算后相加。', complexity: '一科时间 O(sS)，空间 O(S)；每科至多 20 题，每题耗时≤60。',
    bug: { title: '如果把两边的耗时差当作完成时间？', code: 'answer += S - 2 * dp[S/2];', input: '这一科只有耗时 1、2、3、8 的四道题。', answer: 2, why: '错误式子算出两边相差 2；题目要同时完成的时刻 8。区分“差最小”与“较大一边最小”。' },
    checks: ['一科只有一道题时，耗时不会减半', '两边能平分时，完成时间是 S/2', '每科清空 dp，四科用时相加'],
    recall: '两个人同时做事，为什么总用时取 max，而不是和或差？',
  },
  { pid: 'P1507', title: 'NASA 的食物计划', focus: '两个资源要一起记住', kind: 'dual',
    parts: ['食品各有体积、重量和热量，', ['每件最多一次', '仍需保证来源没有使用过当前食品。'], '。总', ['体积和重量都不能超限', '一种资源不能替代另一种，状态必须保留两个容量。'], '，求最大热量。'],
    model: ['dp[h][t] 表示两种容量上限下的最大热量', '只检查体积，重量留到最后判断', '把体积和重量相加，做一个容量'],
    modelErrors: ['忽略重量时可能先保留一个超重的高热量方案，最后再检查已经无法恢复被丢掉的可行方案。', '上限都为 5 时，体积 6、重量 1 的和为 7，虽然不超过 10，体积却已经超限。'],
    insight: '两种资源限制互相独立。只记录一种，可能保留已经违反另一限制的方案。',
    mini: { capacity: 5, weightLimit: 5, items: [{ weight: 2, mass: 5, value: 9 }, { weight: 3, mass: 4, value: 8 }, { weight: 2, mass: 1, value: 2 }] },
    prediction: '体积、重量上限都是 5，这三件食品最多提供多少热量？', answer: 10, reasoning: '第二、三件体积 3+2=5、重量 4+1=5、热量 8+2=10；第一件不能再搭第三件，因为重量超限。',
    state: 'dp[h][t]：体积不超过 h、重量不超过 t 的最大热量。当前食品的体积 volume、重量 weight、热量 energy。',
    line: 'dp[h][t] = max(dp[h][t], dp[h - volume][t - weight] + energy);', source: '两个容量都扣掉当前食品的消耗，再从上一轮的对应状态加热量。',
    initial: '二维 dp 初始全 0：没有食品时，任意容量上限都对应空方案。', loop: '每件食品一轮；h 从 H 倒序到 volume，t 从 T 倒序到 weight。', output: '输出 dp[H][T]，下标是容量上限，不是食品数量。', complexity: '时间 O(nHT)，空间 O(HT)；H、T≤400，n≤50。',
    bug: { title: '如果只检查体积？', code: 'dp[h] = max(dp[h], dp[h-volume] + energy);', input: '体积、重量上限均为 5。两件食品 (体积 2，重量 5，热量 9)、(3，4，8)。', answer: 17, why: '错误程序同时拿两件，热量 17，但总重量为 9。正确答案是 9。把另一维故意设紧，就能暴露遗漏约束。' },
    checks: ['体积够、重量不够的食品不能选', '两种容量都恰好满足时要更新', '只有一件食品，不能在二维循环中重复使用'],
    recall: '以后多出一种独立限制，怎样判断状态是否漏掉了它？',
  },
];
export const guidedId = pid => `lab:luogu:${pid}`;

export function matchesGuidedProblem(row, pid) {
  if (row.id === guidedId(pid) || row.aliasIds?.includes(guidedId(pid))) return true;
  try {
    const url = new URL(row.url);
    return url.hostname.replace(/^www\./, '') === 'luogu.com.cn' && url.pathname.replace(/\/+$/, '') === `/problem/${pid}`;
  } catch { return false; }
}

export function bestMiniPlan(problem) {
  const { items, capacity, weightLimit } = problem.mini, balance = problem.kind === 'balance';
  const total = items.reduce((sum, item) => sum + item.weight, 0);
  let best = balance ? Infinity : -1, picks = [];
  for (let mask = 0; mask < 2 ** items.length; mask++) {
    const chosen = items.filter((_, i) => mask & (1 << i));
    const weight = chosen.reduce((sum, item) => sum + item.weight, 0), mass = chosen.reduce((sum, item) => sum + (item.mass || 0), 0);
    if (!balance && (weight > capacity || (weightLimit != null && mass > weightLimit))) continue;
    const score = balance ? Math.max(weight, total - weight) : chosen.reduce((sum, item) => sum + item.value, 0);
    if (balance ? score < best : score > best) { best = score; picks = items.map((_, i) => i).filter(i => mask & (1 << i)); }
  }
  return picks;
}

export function matchesTransition(input, expected) {
  const normalize = text => text.replace(/\s|;|std::/g, '');
  const parse = text => normalize(text).match(/^(.*?)=max\((.*),(.*)\)$/);
  const actual = parse(input), reference = parse(expected);
  return !!actual && actual[1] === reference[1] && [actual[2], actual[3]].sort().join('|') === [reference[2], reference[3]].sort().join('|');
}
