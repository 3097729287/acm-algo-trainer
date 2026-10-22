export const CHAPTERS = [
  { id: 'pack', title: '先装一次背包', verb: '体验', goal: '亲眼看到：局部最好的选择，不一定拼成最好的方案。', checks: ['pack', 'greedy'] },
  { id: 'state', title: '读懂表格', checks: ['state', 'transition'] },
  { id: 'trace', title: '理解倒序', checks: ['loop', 'repeat'] },
  { id: 'code', title: '写出 C++', checks: ['template'] },
  { id: 'debug', title: '找出错误', checks: ['debug-loop', 'debug-exact', 'debug-boundary'] },
  { id: 'transfer', title: '辨认模型', checks: ['signal-time', 'signal-coins', 'signal-fraction', 'signal-scale'] },
  { id: 'practice', title: '独立练习', checks: ['practice-basic', 'practice-exact', 'practice-partition'] },
];
export const CHECK_IDS = CHAPTERS.flatMap(chapter => chapter.checks);

export const RECOGNITION = [
  { id: 'signal-time', title: '周末任务安排', text: '你有 7 小时。每个任务只能做一次，耗时和收益已知；总耗时不能超过 7，求最大收益。',
    choices: [{ id: 'once', label: '0/1 背包：时间作容量', feedback: '时间是有限资源，任务是物品，每件一次，收益取最大。先写 dp[c] = 耗时不超过 c 的最大收益，再倒序枚举时间。' }, { id: 'unlimited', label: '完全背包：反复做同一任务', feedback: '题目限定每个任务只能做一次。检查选择次数，比看到“收益最大”更关键。' }, { id: 'greedy', label: '总选收益最大的任务', feedback: '高收益任务可能挤掉更好的组合。回想最开始的背包反例。' }], answer: 'once' },
  { id: 'signal-coins', title: '换个目标，还能直接套吗？', text: '面额为 1、3、4 的硬币每种无限枚，凑出恰好 6 元，求最少枚数。金额很小。',
    choices: [{ id: 'once', label: '0/1 背包，倒序取最大', feedback: '一枚 3 元硬币可以再拿一枚，且目标是“最少枚数”。次数和最优目标都改变了。' }, { id: 'unlimited', label: '完全背包，正序取最小', feedback: 'dp[s] = 恰好凑出 s 的最少枚数；dp[0]=0，其余为 INF。正序允许重复，dp[s]=min(dp[s],dp[s-coin]+1)。6 元可用 3+3，共 2 枚。' }, { id: 'greedy', label: '每次取最大面额', feedback: '贪心得到 4+1+1，共 3 枚；3+3 只要 2 枚。' }], answer: 'unlimited' },
  { id: 'signal-fraction', title: '可以切开的补给', text: '补给能按任意比例分装，收益随重量成比例。总载重有限，求最大收益。没有别的约束。',
    choices: [{ id: 'once', label: '必须按整数容量做 0/1 背包', feedback: '这次可以切开物品，整件“选或不选”的限制消失了。先检查模型条件。' }, { id: 'greedy', label: '按单位重量收益从高到低装', feedback: '可以切分时，低性价比的重量总能替换成等重的高性价比补给。最初反例成立的关键，就是物品不可切分。' }, { id: 'unlimited', label: '完全背包，物品无限使用', feedback: '可切分不等于无限供应。这里仍然只能使用现有的补给。' }], answer: 'greedy' },
  { id: 'signal-scale', title: '模型对了，规模呢？', text: '36 件物品，每件最多一次，容量 W 可达 10¹²，重量与价值都为正整数。你想开 dp[W+1]。',
    choices: [{ id: 'capacity', label: '直接 O(nW)，开大数组就行', feedback: '10¹² 个 long long 约需 8 TB，时间也不可行。认识模型之后，还要估计状态数。' }, { id: 'scale', label: '先换枚举维度，考虑折半枚举', feedback: '36 件可分成两半，每半约 2¹⁸ 个子集，分别枚举重量与价值，再合并。本节只要求发现 O(nW) 不可行；折半枚举留待后续学习。' }, { id: 'up', label: '改成正序就能降到 O(n)', feedback: '正倒序都要枚举容量，不改变 O(nW)，而且正序会改变物品的使用次数。' }], answer: 'scale' },
];

export const MISSIONS = [
  { id: 'practice-basic', title: '01 / 自己完成一个新背包', tag: '直接建模', text: '总预算 7 元，三件礼物只能各买一次：(价格 4，快乐值 7)、(3，5)、(2，4)。允许剩钱。最大快乐值是多少？', answer: 12,
    hints: ['先把价格当作重量，预算当作容量。每件礼物最多一次。', '定义 dp[c] 为花费不超过 c 的最大快乐值。初值全 0，价格循环倒序。', '选前两件花 4+3=7，快乐值 7+5=12。第三件不必选；遍历容量会自动比较这些组合。'],
    takeaway: '入口：有限预算 + 独立选项 + 每个一次 + 最大收益 → 0/1 背包。' },
  { id: 'practice-exact', title: '02 / 一句话改变了初始化', tag: '边界迁移', text: '容量必须恰好装满 5。两件物品分别为 (重量 2，价值 4)、(重量 4，价值 9)，每件只能用一次。最大价值是多少？不能装满时输入“不可达”。', answer: '不可达',
    hints: ['先别急着最大化价值。有哪些总重量真的能出现？', '两件物品的可达总重量只有 0、2、4、6，5 不在其中。dp[0]=0，其余不可达。', '答案是不可达。“最多 5”可以拿重量 4 得到价值 9，但这不满足“恰好 5”。转移前检查来源可达。'],
    takeaway: '入口：“恰好”先处理可达性；默认全 0 会把不存在的状态伪装成合法方案。' },
  { id: 'practice-partition', title: '03 / 题面里没有背包', tag: '独立转化', text: '把耗时为 1、2、3、8 的四项工作分给两个人，每项只能分给一个人。两人总耗时的差最小是多少？', answer: 2,
    hints: ['总耗时 14。让其中一人的耗时尽量接近 7，且不超过 7。', '把每项工作的“重量”和“价值”都设为它的耗时，容量设为 7。找到不超过 7 的最大子集和。', '可以选 1+2+3=6，另一人分到 8。最小差为 14−2×6=2。容量不超过一半，避免两边重复考虑。'],
    takeaway: '入口：二分组接近平衡 → 选一组接近总和一半 → 0/1 子集和。' },
];
