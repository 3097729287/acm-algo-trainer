import {canonicalKnowledgeName,matchesKnowledge,compileKnowledge} from '../lib/knowledgeNames.js';
export const STATES = ["未做", "不会", "待重写", "复现AC", "独立AC", "巩固"];
export const STATE_CLASS = [
  "new",
  "stuck",
  "rewrite",
  "reproduce",
  "independent",
  "mastered",
];
export const QUEUES = [
  {
    id: "rewrite",
    name: "待重写",
    desc: "先把看过的题独立写出来",
    color: "pink",
  },
  { id: "fill", name: "待补题", desc: "重新思考，再查阅题解", color: "orange" },
  {
    id: "review",
    name: "间隔复习",
    desc: "AC 后第 7 天，再做一次",
    color: "blue",
  },
  {
    id: "check",
    name: "巩固抽检",
    desc: "巩固后第 30 天，检查掌握",
    color: "green",
  },
];
export const mastered = (row) => ["独立AC", "巩固"].includes(row.status);
export const passed = (row) =>
  ["复现AC", "独立AC", "巩固"].includes(row.status);
export function compileSearch(query) {
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return () => true;
  const predicates=words.map(word=>{
    const range = word.match(/^(\d+)\s*[-~～]\s*(\d+)$/);
    if (range) {const low=Number(range[1]),high=Number(range[2]);return row=>row.difficulty!=null&&row.difficulty>=low&&row.difficulty<=high;}
    if (/^\d+$/.test(word))
      return (row,title) => (
        String(row.difficulty ?? "") === word ||
        String(row.contest || "").toLowerCase().includes(word) ||
        (words.length > 1 && title.includes(word))
      );
    if (/^[a-z]\d?$/.test(word))
      return (row,title) => String(row.problem || "").toLowerCase() === word || (words.length > 1 && title.includes(word));
    return (row,title,status) => [row.contest, row.title, row.knowledge, status, row.platform]
      .join(" ")
      .toLowerCase()
      .replaceAll(" ", "")
      .includes(word.replaceAll(" ", ""));
  });
  return (row,status=row.status) => {const title=String(row.title||'').toLowerCase();return predicates.every(test=>test(row,title,status));};
}
export function matches(row, query) {
  return compileSearch(query)(row);
}
export function compareSearchRelevance(a, b, query) {
  const phrase = query.trim().toLocaleLowerCase();
  if (!phrase) return 0;
  return Number(String(b.title || "").toLocaleLowerCase() === phrase) -
    Number(String(a.title || "").toLocaleLowerCase() === phrase);
}
export function filteredRows(
  rows,
  {
    query = "",
    status = "",
    platform = "",
    tags = null,
    min = "",
    max = "",
    sort = "contest",
    desc = false,
  },
) {
  return rows
    .filter(
      (r) =>
        matches(r, query) &&
        (!status || r.status === status) &&
        (!platform || r.platform === platform) &&
        (!tags || matchesKnowledge(r,tags)) &&
        (min === "" || (r.difficulty != null && r.difficulty >= Number(min))) &&
        (max === "" || (r.difficulty != null && r.difficulty <= Number(max))),
    )
    .sort((a, b) => {
      const relevance = compareSearchRelevance(a, b, query);
      if (relevance) return relevance;
      let result;
      if (sort === "difficulty")
        result = (a.difficulty ?? -1) - (b.difficulty ?? -1);
      else if (sort === "date") result = a.date.localeCompare(b.date);
      else if (sort === "title")
        result = a.title.localeCompare(b.title, "zh-CN");
      else
        result =
          a.contest.localeCompare(b.contest, "zh-CN", { numeric: true }) ||
          a.problem.localeCompare(b.problem, "en", { numeric: true });
      return desc ? -result : result;
    });
}
export function categoryStats(node, rows) {
  const tags = node.tags || [node.name];
  const matched = rows.filter(compileKnowledge(tags));
  return {
    total: matched.length,
    passed: matched.filter(passed).length,
    weak: matched.filter((r) => ["不会", "待重写"].includes(r.status)).length,
  };
}
// Display groups keep the dictionary's standard tags and existing branches intact.
export function organizeCategories(source) {
  const normalize=node=>({...node,name:node.children?.length?node.name:canonicalKnowledgeName(node.name),tags:[...new Set((node.tags||[]).map(canonicalKnowledgeName))],children:(node.children||[]).map(normalize)});
  const pending=new Map(source.map(normalize).map(node=>[node.name,node]));
  const take=names=>names.map(name=>{const node=pending.get(name);pending.delete(name);return node}).filter(Boolean);
  const group=(name,children)=>({name,children,tags:[...new Set(children.flatMap(n=>n.tags||[n.name]))]});
  const nodes=[];
  const add=(name,names)=>{const existing=take([name])[0],children=[...(existing?.children||[]),...take(names.filter(label=>label!==name))];if(existing||children.length)nodes.push({...group(name,children),tags:[...new Set([...(existing?.tags||[]),...children.flatMap(node=>node.tags||[])])]})};
  add('思维与策略',['模拟','枚举','贪心','构造','排序','折半枚举']);
  const dp=take(['动态规划','线性 DP','DP']);if(dp.length)nodes.push({...dp[0],name:'动态规划'});
  add('基础技巧',['前缀和与差分','二分','双指针','位运算','离散化','连续段','递推','倍增']);
  const structures=take(['数据结构']);if(structures.length){const extra=take(['莫队']);nodes.push(group('数据结构',[...structures[0].children,...extra]))}
  const graphs=take(['图论']);nodes.push(...graphs);
  add('数学与计数',['数学','计数','置换环']);
  const strings=take(['字符串']);nodes.push(...strings);
  const search=take(['搜索']);nodes.push(...search);
  add('计算几何',['计算几何','扫描线']);
  if(pending.size)nodes.push(group('专题方法',[...pending.values()]));
  return nodes;
}
