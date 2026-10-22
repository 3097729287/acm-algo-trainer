import {compareContestNewest} from './practiceMetadata.js';

export function catalogSegments(row) {
  const name=row.contest||row.name||'其他题目',fullName=`${name} ${row.contestFullName||''}`;
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
  if (!path.length)return ['Codeforces','AtCoder','牛客','洛谷','ACM','蓝桥杯 B 组'];
  if (path.length===1&&path[0]==='AtCoder')return ['ABC','ARC','AGC'];
  if (path.length===1&&path[0]==='ACM')return ['ICPC','CCPC','网络预选赛','省赛','邀请赛','总决赛','分区赛'];
  if (path.length===1&&path[0].startsWith('蓝桥杯'))return ['省赛','国赛'];
  return [];
}

export function contestOptions(events,{descending=true,shelf=''}={}) {
  const roots=[];
  const ensure=(parts)=>{let nodes=roots;for(const label of parts){let folder=nodes.find(node=>node.value===undefined&&node.label===label);if(!folder){folder={label,children:[]};nodes.push(folder);}nodes=folder.children;}return nodes;};
  if(!shelf)for(const name of catalogFolders())ensure([name]);
  for(const item of events){const parts=catalogSegments({...item,contest:item.displayName||item.name}),nodes=ensure(parts.slice(0,-1));nodes.push({label:`${parts.at(-1)} · ${item.count} 题`,selectionLabel:`${item.displayName||item.name} · ${item.count} 题`,value:item.name,event:item});}
  for(const root of roots)for(const name of catalogFolders([root.label]))ensure([root.label,name]);
  const sort=nodes=>{nodes.sort((a,b)=>a.event&&b.event?compareContestNewest(a.event,b.event)*(descending?1:-1):/^20\d{2}年$/.test(a.label)&&/^20\d{2}年$/.test(b.label)?b.label.localeCompare(a.label)*(descending?1:-1):a.label.localeCompare(b.label,'zh-CN',{numeric:true}));nodes.forEach(node=>node.children&&sort(node.children));};
  sort(roots);return roots;
}
