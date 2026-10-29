// Keep literals, comments and preprocessing tokens intact while adapting C++
// type spellings. In particular, "unsigned long long" is not "unsigned ll".
function cppSegments(source) {
 const parts=[];let start=0,index=0;
 while(index<source.length){
  const rest=source.slice(index),raw=rest.match(/^(?:u8|u|U|L)?R"([^\s()\\]{0,16})\(/);
  let end=null;
  if(raw){const marker=')'+raw[1]+'"',close=source.indexOf(marker,index+raw[0].length);end=close<0?source.length:close+marker.length;}
  else if(rest.startsWith('//')){const close=source.indexOf('\n',index);end=close<0?source.length:close;}
  else if(rest.startsWith('/*')){const close=source.indexOf('*/',index+2);end=close<0?source.length:close+2;}
  else if(source[index]==='"'||source[index]==="'"&&!(/\b(?:0[xX][0-9a-f]+|[0-9][0-9a-f]*)$/i.test(source.slice(0,index))&&/[0-9a-f]/i.test(source[index+1]||''))){
   const quote=source[index];let next=index+1;
   while(next<source.length){if(source[next]==='\\'){next+=2;continue;}if(source[next++]===quote)break;}end=next;
  }
  if(end!==null){if(index>start)parts.push({code:true,text:source.slice(start,index)});parts.push({code:false,text:source.slice(index,end)});index=end;start=end;}else index++;
 }
 if(start<source.length)parts.push({code:true,text:source.slice(start)});return parts;
}
function maskCpp(source){return cppSegments(source).map(part=>part.code?part.text:part.text.replace(/[^\n]/g,' ')).join('');}
function lines(source){return source.match(/[^\n]*\n|[^\n]+$/g)||[];}
// This boundary never enters a function or an open #if block. Header comments,
// complete conditional headers, macros and existing aliases stay above it.
// New ll declarations use the header-only boundary, before any alias using ll.
function preambleEnd(source,{aliases=true}={}){
 const masked=maskCpp(source);let position=0,conditional=0,conditionalStart=0;
 while(position<masked.length){
  const blank=masked.slice(position).match(/^\s*/)[0].length;position+=blank;
  if(position===masked.length)break;
  const start=position,rest=masked.slice(start),directive=rest.match(/^#\s*(\w+)/)?.[1];
  if(directive){
   if(/^(if|ifdef|ifndef)$/.test(directive)){if(!conditional)conditionalStart=start;conditional++;}
   if(directive==='endif')conditional=Math.max(0,conditional-1);
   do{const end=source.indexOf('\n',position),next=end<0?source.length:end+1,line=source.slice(position,next);position=next;if(!/\\\r?\n$/.test(line))break;}while(position<source.length);
   continue;
  }
  if(conditional){if(!aliases)return conditionalStart;const end=masked.indexOf('\n',position);position=end<0?masked.length:end+1;continue;}
  if(/^using\s+namespace\b/.test(rest)||aliases&&/^(?:using|typedef)\b/.test(rest)){
   let braces=0,parens=0,brackets=0,found=false;
   for(let cursor=start;cursor<masked.length;cursor++){
    const char=masked[cursor];if(char==='{')braces++;if(char==='}')braces--;if(char==='(')parens++;if(char===')')parens--;if(char==='[')brackets++;if(char===']')brackets--;
    if(char===';'&&!braces&&!parens&&!brackets){position=cursor+1;found=true;break;}
   }
   if(found)continue;
  }
  return start;
 }return conditional?conditionalStart:position;
}
function globalAt(mask,offset){
 let braces=0,branch=0,continuation=false;
 for(const line of lines(mask.slice(0,offset))){
  const directive=line.match(/^\s*#\s*(\w+)/)?.[1];
  if(continuation||directive){if(!line.endsWith('\n'))return false;if(/^(if|ifdef|ifndef)$/.test(directive||''))branch++;if(directive==='endif')branch=Math.max(0,branch-1);continuation=/\\\r?\n$/.test(line);continue;}
  braces+=(line.match(/{/g)||[]).length-(line.match(/}/g)||[]).length;
 }return !braces&&!branch;
}
function llDefinitions(source){
 const mask=maskCpp(source);
 return {alias:[...mask.matchAll(/\busing\s+ll\s*=\s*([^;]+);|\btypedef\s+([^;]+)\s+ll\s*;/g)].find(match=>globalAt(mask,match.index)),
  macro:[...mask.matchAll(/^\s*#\s*define\s+ll\s+([^\n]+)/gm)].find(match=>globalAt(mask,match.index))};
}
export function normalizeCppTemplate(source=''){
 const mask=maskCpp(source),{alias,macro}=llDefinitions(source);
 if(alias&&!/^(?:signed\s+)?long\s+long(?:\s+int)?$/.test((alias[1]||alias[2]).trim()))return source;
 if(macro&&!/^(?:signed\s+)?long\s+long(?:\s+int)?$/.test(macro[1].trim()))return source;
 const protectedAliases=[...mask.matchAll(/\busing\s+ll\s*=[^;]+;|\btypedef\s+[^;]+\s+ll\s*;/g)].map(match=>[match.index,match.index+match[0].length]);
 let preprocessor=false,position=0;
 let result=cppSegments(source).map(part=>{
  const base=position;position+=part.text.length;
  if(!part.code)return part.text;let lineStart=base;
  return lines(part.text).map(line=>{
   const at=lineStart;lineStart+=line.length;
   const directive=preprocessor||/^\s*#/.test(line);preprocessor=directive&&/\\\s*$/.test(line);
   if(directive||/\b(?:using\s+ll\s*=|typedef\s+[^;]*\bll\s*;)/.test(line))return line;
   return line.replace(/\b(unsigned\s+)?(?:signed\s+)?long\s+long(?:\s+int)?\b/g,(match,unsigned,offset)=>unsigned||/\b(?:unsigned|signed)\s*$/.test(mask.slice(0,at+offset))||protectedAliases.some(([start,end])=>at+offset>=start&&at+offset<end)?match:'ll');
  }).join('');
 }).join('');
 if(!alias&&!macro){const at=preambleEnd(result,{aliases:false});result=result.slice(0,at)+(at&&result[at-1]!=='\n'?'\n':'')+'using ll = long long;\n'+result.slice(at);}
 return result;
}
export function templateForDisplay(item){
 if(item?.language!=='cpp17'||!item.builtin)return item;
 return {...item,code:normalizeCppTemplate(item.code),...(item.contestCode?{contestCode:normalizeCppTemplate(item.contestCode)}:{})};
}
function topLevelLines(source){
 const masked=lines(maskCpp(source)),original=lines(source);let branch=0,braces=0;
 return original.map((text,index)=>{
  const code=masked[index]||'',directive=code.match(/^\s*#\s*(\w+)/)?.[1],global=branch===0&&braces===0;
  if(/^(if|ifdef|ifndef)$/.test(directive||''))branch++;
  if(directive==='endif')branch=Math.max(0,branch-1);
  if(!directive)braces+=(code.match(/{/g)||[]).length-(code.match(/}/g)||[]).length;
  return {text,code,global};
 });
}
export function insertTemplate(current='',template='',language='cpp17'){
 if(!template.trim())return current;
 if(language!=='cpp17')return template.trimEnd()+'\n\n'+current;
 const at=preambleEnd(current),prefix=current.slice(0,at),includes=new Set(),namespaces=new Set(),{alias,macro}=llDefinitions(prefix);
 const hasAlias=Boolean(alias||macro);
 if(alias&&!/^(?:signed\s+)?long\s+long(?:\s+int)?$/.test((alias[1]||alias[2]).trim()))throw Error('当前代码的 ll 已有其它类型定义，请先统一类型后插入模板。');
 if(macro&&!/^(?:signed\s+)?long\s+long(?:\s+int)?$/.test(macro[1].trim()))throw Error('当前代码的 ll 宏已有其它定义，请先统一类型后插入模板。');
 for(const {text,code,global} of topLevelLines(prefix))if(global){
  const include=/^\s*#\s*include\b/.test(code)?text.match(/^\s*#\s*include\s*([<"][^>"\n]+[>"])/)?.[1]:null;if(include)includes.add(include);
  const ns=code.match(/^\s*using\s+namespace\s+([^;]+);\s*$/)?.[1];if(ns)namespaces.add(ns.trim());
 }
 const normalized=normalizeCppTemplate(template);
 const templateMask=maskCpp(normalized);
 const aliasRanges=hasAlias?[...templateMask.matchAll(/\busing\s+ll\s*=[^;]+;|\btypedef\s+[^;]+\s+ll\s*;/g)].filter(match=>globalAt(templateMask,match.index)).map(match=>[match.index,match.index+match[0].length]):[];
 const prepared=aliasRanges.reduceRight((text,[start,end])=>text.slice(0,start)+text.slice(end),normalized);
 const payload=topLevelLines(prepared).filter(({text,code,global})=>{
  if(!global)return true;
  const include=/^\s*#\s*include\b/.test(code)?text.match(/^\s*#\s*include\s*([<"][^>"\n]+[>"])/)?.[1]:null;
  if(include){if(includes.has(include))return false;includes.add(include);}
  const ns=code.match(/^\s*using\s+namespace\s+([^;]+);\s*$/)?.[1];if(ns&&namespaces.has(ns.trim()))return false;
  return true;
 }).map(line=>line.text).join('').trim();
 return current.slice(0,at).trimEnd()+(at?'\n\n':'')+payload+'\n\n'+current.slice(at).replace(/^\s*\n/,'');
}
