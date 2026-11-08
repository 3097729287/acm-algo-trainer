import {cppLanguage} from '@codemirror/lang-cpp';
import {pythonLanguage} from '@codemirror/lang-python';
import {classHighlighter,highlightTree} from '@lezer/highlight';

const LIMIT=65536;
export function editorialLanguage(className='',source=''){
 const name=className.match(/language-([^\s]+)/)?.[1]?.toLowerCase();
 if(['cpp','c++','cxx','cc','cplusplus','cpp11','cpp14','cpp17','cpp20','cpp23','c++11','c++14','c++17','c++20','c++23','c','c99','c11'].includes(name))return 'cpp17';
 if(['python','python3','py','py3'].includes(name))return 'python3';
 return !name&&/^\s*#\s*include\s*[<"]/m.test(source)?'cpp17':null;
}

// Change only an unused increment of an integer declared by that for loop.
// Prefix increments in conditions, calls, literals and user code stay intact.
function codeMask(source){
 const spans=[];let i=0;
 while(i<source.length){
  const start=i,rest=source.slice(i);let end;
  if(rest.startsWith('//')){end=source.indexOf('\n',i+2);if(end<0)end=source.length;}
  else if(rest.startsWith('/*')){end=source.indexOf('*/',i+2);end=end<0?source.length:end+2;}
  else{
   const raw=rest.match(/^(?:u8|u|U|L)?R"([^ ()\\\t\r\n]{0,16})\(/);
   if(raw){const delimiter=')'+raw[1]+'"',close=source.indexOf(delimiter,i+raw[0].length);end=close<0?source.length:close+delimiter.length;}
   else{
    const quoted=rest.match(/^(?:u8|u|U|L)?(["'])/);
    if(quoted&&!(quoted[0]==="'"&&/[\w]/.test(source[i-1]||'')&&/[\w]/.test(source[i+1]||''))){
    const quote=quoted[1];end=i+quoted[0].length;
    for(;end<source.length;end++){if(source[end]==='\\')end++;else if(source[end]===quote){end++;break;}}
    }
   }
  }
  if(end!=null){spans.push([start,end]);i=end;}else i++;
 }
 let mask=source;for(const [start,end]of spans.toReversed())mask=mask.slice(0,start)+' '.repeat(end-start)+mask.slice(end);
 return mask;
}
export function normalizeEditorialCode(source,language){
 if(language!=='cpp17'||source.length>LIMIT)return source;
 const edits=[],mask=codeMask(source);
 const collect=(node,names,header,offset)=>{
  if(node.name==='UpdateExpression'){
   const value=header.slice(node.from,node.to),match=value.match(/^\+\+\s*([A-Za-z_]\w*)$/);
   if(match&&names.has(match[1]))edits.push({from:offset+node.from,to:offset+node.to,text:match[1]+'++'});
  }else if(['CommaExpression','ParenthesizedExpression'].includes(node.name)){
   for(let child=node.firstChild;child;child=child.nextSibling)collect(child,names,header,offset);
  }
 };
 // Parse each header independently. A fragment or a deeply nested body can
 // otherwise cause error recovery to hide unrelated, valid for declarations.
 for(const match of mask.matchAll(/\bfor\s*\(/g)){
  let end=match.index+match[0].length,depth=1;
  for(;end<mask.length&&depth;end++){if(mask[end]==='(')depth++;else if(mask[end]===')')depth--;}
  if(depth)continue;
  const header=source.slice(match.index,end),loop=cppLanguage.parser.parse(header+' {}').topNode.getChild('ForStatement');
  const declaration=loop?.getChild('Declaration');if(!declaration)continue;
  const declarators=declaration.getChildren('InitDeclarator');
  const typeName=declarators.length&&header.slice(declaration.from,declarators[0].from).trim();
  const integer=typeName&&(/^(?:(?:unsigned|signed|long|short)\s*)*(?:int|char|wchar_t|char16_t|char32_t)?$/.test(typeName)||/^(?:std\s*::\s*)?(?:size_t|ptrdiff_t|u?int(?:8|16|32|64|ptr|max)_t|u?int_(?:least|fast)(?:8|16|32|64)_t)$/.test(typeName));
  if(!integer)continue;
  const names=new Set(declarators.map(item=>item.getChild('Identifier')).filter(Boolean).map(item=>header.slice(item.from,item.to)));
  let previous=null;for(let child=loop.firstChild;child;child=child.nextSibling){if(child.name===')'){if(previous)collect(previous,names,header,match.index);break;}previous=child;}
 }
 for(const edit of edits.sort((a,b)=>b.from-a.from))source=source.slice(0,edit.from)+edit.text+source.slice(edit.to);
 return source;
}

export function editorialTokens(source,language){
 if(!language||source.length>LIMIT)return [{text:source,classes:''}];
 const parser=language==='python3'?pythonLanguage.parser:cppLanguage.parser,parts=[];let position=0;
 highlightTree(parser.parse(source),classHighlighter,(from,to,classes)=>{
  if(from>position)parts.push({text:source.slice(position,from),classes:''});
  parts.push({text:source.slice(from,to),classes});position=to;
 });
 if(position<source.length)parts.push({text:source.slice(position),classes:''});
 return parts;
}

const caches=new WeakMap();let queue=Promise.resolve();
const currentOwner=()=>String(window.__tbAccountUserId||'local');
export function formatEditorialCode(api,id,source,language){
 const owner=currentOwner();let store=caches.get(api);
 if(!store||store.owner!==owner){store={owner,values:new Map()};caches.set(api,store);}
 const key=JSON.stringify([id,language,source]);if(store.values.has(key))return store.values.get(key);
 const task=queue.catch(()=>{}).then(async()=>{
  if(currentOwner()!==owner)throw Error('Retired reading account');
  const value=await api('code/format',{id,language,code:source});
  if(currentOwner()!==owner||typeof value.code!=='string')throw Error('Retired code format');
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(source));
  const expected=[...new Uint8Array(digest)].map(byte=>byte.toString(16).padStart(2,'0')).join('');
  if(value.inputSha256!==expected)throw Error('Code format input changed');
  return value.code;
 });
 queue=task.catch(()=>{});store.values.set(key,task);
 while(store.values.size>32)store.values.delete(store.values.keys().next().value);
 task.catch(()=>{if(store.values.get(key)===task)store.values.delete(key);});
 return task;
}
