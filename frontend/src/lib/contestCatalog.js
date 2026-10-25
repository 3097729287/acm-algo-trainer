import {compareContestNewest} from './practiceMetadata.js';

export function catalogSegments(row) {
  const name=row.contest||row.name||'其他题目',fullName=`${name} ${row.contestFullName||''}`;
  if (row.labTopic) return ['算法实验室', row.labTopic, name];
  if (row.schoolTraining || /^https:\/\/(?:codeforces.com\/gym\/726517|ac.nowcoder.com\/acm\/contest\/142622)\//.test(row.url || '')) return ['校队训练', name];
  if (/蓝桥/.test(`${fullName} ${row.series||''}`)) {
    const group=/(?:B\s*组|大学B(?:\s|$)|组\s*B)/i.test(`${fullName} ${row.examGroup||''}`)?'蓝桥杯 B 组':'蓝桥杯';
    const year=fullName.match(/20\d{2}/)?.[0]||row.examYear;
    return [group,/国赛|决赛/.test(`${fullName} ${row.examStage||''}`)?'国赛':'省赛',year?`${year}年`:'年份待核实',name];
  }
  if (row.series==='XCPC'||/ICPC|CCPC|XCPC|ACM|区域赛|邀请赛|省赛|网络.*赛/i.test(fullName)) {
    const type=/网络|预选|online|qualification/i.test(fullName)?'网络预选赛'
      :/省赛|省(?:第[一二三四五六七八九十\d]+届)?(?:ICPC|CCPC|大学生|程序)/i.test(fullName)?'省赛'
      :/邀请|invitational/i.test(fullName)?'邀请赛'
      :/总决赛|world finals/i.test(fullName)?'总决赛'
      :/分区赛|subregional/i.test(fullName)?'分区赛'
      :/CCPC/i.test(fullName)?'CCPC':/ICPC/i.test(fullName)?'ICPC':'其他赛事';
    const year=fullName.match(/20\d{2}/)?.[0]||String(row.contestDate||row.startedAt||'').match(/^20\d{2}/)?.[0];
    const event=name.replace(/[（(]\s*(?:热身赛?|正式赛|正赛|warm.?up)\s*[）)]/gi,'').trim();
    return ['ACM',type,year?`${year}年`:'年份待核实',event,/热身|warm.?up/i.test(fullName)?'热身赛':'正赛'];
  }
  const series=row.series&&row.series!==row.platform?row.series:name.match(/练习赛|小白月赛|周赛|月赛|挑战赛|入门赛|基础赛|教育赛|ABC|ARC|AGC|Div\.?\s*[1-4](?:\s*\+\s*Div\.?\s*[1-4])?/i)?.[0]||'其他比赛';
  return [row.platform||'其他平台',series,name];
}

// Known series remain discoverable even when none of their contests is bundled.
// Entering an empty folder states that explicitly; it never invents a contest.
export function catalogFolders(path=[]) {
  if (!path.length)return ['Codeforces','AtCoder','牛客','洛谷','ACM','蓝桥杯 B 组','校队训练'];
  if (path.length===1&&path[0]==='AtCoder')return ['ABC','ARC','AGC'];
  if (path.length===1&&path[0]==='ACM')return ['ICPC','CCPC','网络预选赛','省赛','邀请赛','总决赛','分区赛'];
  if (path.length===1&&path[0].startsWith('蓝桥杯'))return ['省赛','国赛'];
  return [];
}

// Collapse navigation-only nodes while keeping their original paths for saved filters.
const isYear = label => /^20\d{2}年$/.test(label) || label === '年份待核实';
const preserveFolder = (parent, label) => catalogFolders(parent).includes(label) || (!parent.length && label === '算法实验室');
export function compactCatalogOptions(nodes, parent = []) {
  return nodes.flatMap(node => {
    const path = [...parent, node.label];
    const children = node.children?.length ? compactCatalogOptions(node.children, path) : undefined;
    const current = {...node, children};
    if (!children) return [{...current, label: node.selectionLabel || node.label}];
    if (parent[0]?.startsWith('蓝桥杯') && isYear(node.label)) return children;
    if (children.length === 1 && !preserveFolder(parent, node.label)) return children;
    return [current];
  });
}

export function catalogEntries(rows, path = []) {
  const selected = rows.filter(row => path.every((part, i) => catalogSegments(row)[i] === part));
  const groups = new Map(catalogFolders(path).map(label => [label, []]));
  for (const row of selected) {
    const label = catalogSegments(row)[path.length];
    if (!label) continue;
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push(row);
  }
  return [...groups].flatMap(([name, items]) => {
    let next = [...path, name];
    if (path[0]?.startsWith('蓝桥杯') && isYear(name)) return catalogEntries(items, next);
    if (items.length && !preserveFolder(path, name)) {
      while (true) {
        const children = new Set(items.map(row => catalogSegments(row)[next.length]).filter(Boolean));
        if (children.size !== 1 || items.some(row => catalogSegments(row).length === next.length)) break;
        next = [...next, [...children][0]];
      }
    }
    const leaf = items.length > 0 && items.every(row => catalogSegments(row).length === next.length);
    return [{label: leaf ? items[0].contest || items[0].name || name : next.at(-1), path: next, items, leaf}];
  }).sort((a, b) => a.leaf && b.leaf
    ? compareContestNewest({...a.items[0], rows: a.items}, {...b.items[0], rows: b.items})
    : isYear(a.label) && isYear(b.label) ? b.label.localeCompare(a.label)
    : a.label.localeCompare(b.label, 'zh-CN', {numeric: true}));
}

export function contestOptions(events,{descending=true,shelf=''}={}) {
  const roots=[];
  const ensure=(parts)=>{let nodes=roots;for(const label of parts){let folder=nodes.find(node=>node.value===undefined&&node.label===label);if(!folder){folder={label,children:[]};nodes.push(folder);}nodes=folder.children;}return nodes;};
  if(!shelf)for(const name of catalogFolders())ensure([name]);
  if(events.some(item=>item.labTopic))ensure(['算法实验室']);
  for(const item of events){const parts=catalogSegments({...item,contest:item.displayName||item.name}),nodes=ensure(parts.slice(0,-1));nodes.push({label:`${parts.at(-1)} · ${item.count} 题`,selectionLabel:`${item.displayName||item.name} · ${item.count} 题`,value:item.name,event:item});}
  for(const root of roots)for(const name of catalogFolders([root.label]))ensure([root.label,name]);
  const sort=nodes=>{nodes.sort((a,b)=>a.event&&b.event?compareContestNewest(a.event,b.event)*(descending?1:-1):/^20\d{2}年$/.test(a.label)&&/^20\d{2}年$/.test(b.label)?b.label.localeCompare(a.label)*(descending?1:-1):a.label.localeCompare(b.label,'zh-CN',{numeric:true}));nodes.forEach(node=>node.children&&sort(node.children));};
  sort(roots);return compactCatalogOptions(roots);
}

export function contestFilterOptions(rows) {
 const roots=[];
 const ensure=path=>{let nodes=roots,node;for(let i=0;i<path.length;i++){const label=path[i];node=nodes.find(item=>item.label===label);if(!node){node={label,value:JSON.stringify(path.slice(0,i+1)),children:[]};nodes.push(node);}nodes=node.children;}return node;};
 for(const name of catalogFolders())ensure([name]);
 for(const row of rows)if(!row.catalogHidden){const leaf=ensure(catalogSegments(row));leaf.selectionLabel=row.contest||row.name||leaf.label;}
 for(const root of roots)for(const name of catalogFolders([root.label]))ensure([root.label,name]);
 const finish=nodes=>nodes.sort((a,b)=>a.label.localeCompare(b.label,'zh-CN',{numeric:true})).map(node=>{const children=finish(node.children);return {...node,...(children.length?{children}:{children:undefined})};});
 return compactCatalogOptions(finish(roots));
}
