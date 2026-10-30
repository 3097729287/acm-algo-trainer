import {createContestComparator} from './practiceMetadata.js';
import {rowPlatform,PLATFORM_REGISTRY} from './platformRegistry.js';
const folderOrder=new Intl.Collator('zh-CN',{numeric:true});

export function contestYear(row) {
  for(const value of [row.eventYear,row.examYear,row.xcpcYear])if(/^20\d{2}$/.test(String(value||'')))return String(value);
  return `${row.contest||row.name||''} ${row.contestFullName||''}`.match(/20\d{2}/)?.[0]
    ||String(row.contestDate||row.startedAt||row.endedAt||'').match(/^20\d{2}/)?.[0];
}

export function catalogSegments(row) {
  const name=row.contest||row.name||'其他题目',fullName=`${name} ${row.contestFullName||''}`;
  if (row.labTopic || row.source==='algorithm-lab' || row.series==='算法实验室') return ['算法实验室', row.labTopic||name.replace(/^算法实验室\s*·\s*/,''), name];
  if (row.schoolTraining || /^https:\/\/(?:codeforces.com\/gym\/726517|ac.nowcoder.com\/acm\/contest\/142622)\//.test(row.url || '')) return ['校队训练', name];
  if (/蓝桥/.test(`${fullName} ${row.series||''}`)) {
    const group=/(?:B\s*组|大学B(?:\s|$)|组\s*B)/i.test(`${fullName} ${row.examGroup||''}`)?'蓝桥杯 B 组':'蓝桥杯';
    const year=contestYear(row);
    return [group,/国赛|决赛/.test(`${fullName} ${row.examStage||''}`)?'国赛':'省赛',year?`${year}年`:'年份待核实',name];
  }
  if (row.series==='XCPC'||/ICPC|CCPC|XCPC|ACM|区域赛|邀请赛|省赛|网络.*赛/i.test(fullName)) {
    const eventType=`${fullName} ${row.examStage||''} ${row.xcpcKind||''}`;
    const type=/网络|预选|online|qualification/i.test(eventType)?'网络预选赛'
      :/省赛|省(?:第[一二三四五六七八九十\d]+届)?(?:ICPC|CCPC|大学生|程序)|\bprovincial\b/i.test(eventType)?'省赛'
      :/邀请|invitational/i.test(eventType)?'邀请赛'
      :/总决赛|world finals/i.test(eventType)?'总决赛'
      :/分区赛|subregional/i.test(eventType)?'分区赛'
      :/CCPC/i.test(fullName)?'CCPC 区域赛':/ICPC/i.test(fullName)?'ICPC 区域赛':'其他赛事';
    const year=contestYear(row);
    const event=name.replace(/[（(]\s*(?:热身赛?|正式赛|正赛|warm.?up)\s*[）)]/gi,'').trim();
    return ['XCPC',type,year?`${year}年`:'年份待核实',event,/热身|warm.?up/i.test(eventType)?'热身赛':'正赛'];
  }
  const series=row.series&&row.series!==row.platform?row.series:name.match(/练习赛|小白月赛|周赛|月赛|挑战赛|入门赛|基础赛|教育赛|ABC|ARC|AGC|Div\.?\s*[1-4](?:\s*\+\s*Div\.?\s*[1-4])?/i)?.[0]||'其他比赛';
  return [row.platform||'其他平台',series,name];
}

// Event types are exclusive: an invitation/provincial must not appear among regionals.
export function catalogPaths(row){
 const path=catalogSegments(row),platform=rowPlatform(row);
 // XCPC is a platform-independent event category. Hosting provenance stays on
 // the problem for source filters, original links and the submit adapter.
 return platform&&path[0]!==platform&&path[0].startsWith('蓝桥杯')
  ?[path,[platform,...path.slice(1)]]:[path];
}
export function normalizeCatalogPath(path=[]) {
  return path.map((part,index)=>index===0&&part==='ACM'?'XCPC':index===1&&['ACM','XCPC'].includes(path[0])&&['ICPC','CCPC'].includes(part)?`${part} 区域赛`:part);
}
const begins=(parts,path)=>path.every((part,index)=>parts[index]===part);
export const catalogPathMatches=(row,path)=>catalogPaths(row).some(parts=>begins(parts,normalizeCatalogPath(path)));

// Preserve these familiar grouping levels when they contain actual contests.
export function catalogFolders(path=[]) {
  path=normalizeCatalogPath(path);
  if (!path.length)return ['算法实验室',...PLATFORM_REGISTRY.map(platform=>platform.id),'XCPC','蓝桥杯 B 组','校队训练'];
  if (path.length===1&&path[0]==='Codeforces')return ['教育赛','Div.1','Div.2','Div.3','Div.4'];
  if (path.length===1&&path[0]==='AtCoder')return ['ABC','ARC','AGC'];
  if (path.length===1&&path[0]==='XCPC')return ['ICPC 区域赛','CCPC 区域赛','网络预选赛','省赛','邀请赛','总决赛','分区赛'];
  if (path.length===1&&path[0].startsWith('蓝桥杯'))return ['省赛','国赛'];
  return [];
}

// Collapse navigation-only nodes while keeping their original paths for saved filters.
const isYear = label => /^20\d{2}年$/.test(label) || label === '年份待核实';
const preserveFolder = (parent, label) => !parent.length || isYear(label) || catalogFolders(parent).includes(label);
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

export function catalogEntries(rows, path = [], {descending=true}={}) {
  return catalogEntriesFor(rows,normalizeCatalogPath(path),new WeakMap(),descending);
}
function catalogEntriesFor(rows,path,cache,descending){
  const paths=row=>{if(!cache.has(row))cache.set(row,catalogPaths(row));return cache.get(row);};
  const matching=(row,prefix)=>paths(row).filter(parts=>begins(parts,prefix));
  const selected = rows.filter(row => matching(row,path).length);
  const groups = new Map();
  for (const row of selected) {
    for(const label of new Set(matching(row,path).map(parts=>parts[path.length]).filter(Boolean))){
      if (!groups.has(label)) groups.set(label, []);
      groups.get(label).push(row);
    }
  }
  const result=[...groups].flatMap(([name, items]) => {
    let next = [...path, name];
    if (path[0]?.startsWith('蓝桥杯') && isYear(name)) return catalogEntriesFor(items,next,cache,descending);
    if (items.length && !preserveFolder(path, name)) {
      while (true) {
        const branches=items.flatMap(row=>matching(row,next));
        const children = new Set(branches.map(parts=>parts[next.length]).filter(Boolean));
        if (children.size !== 1 || branches.some(parts=>parts.length===next.length)) break;
        next = [...next, [...children][0]];
      }
    }
    const leaf = items.length > 0 && items.every(row => matching(row,next).some(parts=>parts.length===next.length));
    return [{label: leaf ? items[0].contest || items[0].name || name : next.at(-1), path: next, items, leaf}];
  });
  const comparable=new Map(result.filter(item=>item.leaf).map(item=>[item,{...item.items[0],rows:item.items}]));
  const compareNewest=createContestComparator();
  return result.sort((a, b) => (a.leaf && b.leaf
    ? compareNewest(comparable.get(a),comparable.get(b))
    : isYear(a.label) && isYear(b.label) ? b.label.localeCompare(a.label)
    : folderOrder.compare(a.label,b.label))*(descending?1:-1));
}

export function contestOptions(events,{descending=true,shelf=''}={}) {
  const roots=[];
  const ensure=(parts)=>{let nodes=roots;for(const label of parts){let folder=nodes.find(node=>node.value===undefined&&node.label===label);if(!folder){folder={label,children:[]};nodes.push(folder);}nodes=folder.children;}return nodes;};
  for(const item of events)for(const parts of catalogPaths({...item,contest:item.displayName||item.name})){const nodes=ensure(parts.slice(0,-1));nodes.push({label:`${parts.at(-1)} · ${item.expectedCount||item.count} 题`,selectionLabel:`${item.displayName||item.name} · ${item.expectedCount||item.count} 题`,value:item.name,event:item});}
  const compareNewest=createContestComparator();
  const sort=nodes=>{nodes.sort((a,b)=>a.event&&b.event?compareNewest(a.event,b.event)*(descending?1:-1):/^20\d{2}年$/.test(a.label)&&/^20\d{2}年$/.test(b.label)?b.label.localeCompare(a.label)*(descending?1:-1):folderOrder.compare(a.label,b.label));nodes.forEach(node=>node.children&&sort(node.children));};
  sort(roots);return compactCatalogOptions(roots);
}

export function contestFilterOptions(rows) {
 const roots=[];
 const ensure=path=>{let nodes=roots,node;for(let i=0;i<path.length;i++){const label=path[i];node=nodes.find(item=>item.label===label);if(!node){node={label,value:JSON.stringify(path.slice(0,i+1)),children:[]};nodes.push(node);}nodes=node.children;}return node;};
 for(const row of rows)if(!row.catalogHidden)for(const parts of catalogPaths(row)){const leaf=ensure(parts);leaf.selectionLabel=row.contest||row.name||leaf.label;}
 const finish=nodes=>nodes.sort((a,b)=>folderOrder.compare(a.label,b.label)).map(node=>{const children=finish(node.children);return {...node,...(children.length?{children}:{children:undefined})};});
 return compactCatalogOptions(finish(roots));
}
