const names=[[/^1024\s*数学专场考核/,'数学专场'],[/^1101\s*TTC\s*\(Team Training Contest\)/i,'团队模拟1'],[/^1025\s*Graph Theory Assessment/i,'图论专场']];
export function schoolContestName(value){const text=String(value??'');for(const [pattern,title] of names)if(pattern.test(text))return text.replace(pattern,title);return text;}

// A known roster remains selectable while its statements are refreshed. Keep
// the canonical name for API requests, saved filters and historical records.
export function includeSchoolContests(events,rows){
 const result=[...events],groups=new Map();
 for(const row of rows)if(row.schoolTraining){const group=groups.get(row.contest)||[];group.push(row);groups.set(row.contest,group);}
 for(const [name,items] of groups)if(!result.some(event=>event.name===name)){
  const expected=Math.max(...items.map(row=>row.contestProblemCount||0));
  if(!expected||new Set(items.map(row=>row.problem)).size!==expected)continue;
  result.push({name,displayName:schoolContestName(name),count:items.length,expectedCount:expected,complete:false,schoolTraining:true,platform:items[0].platform,series:'校队训练',duration:120,rules:'acm',problemIds:items.map(row=>row.id)});
 }
 return result;
}
