import {cppLanguage} from '@codemirror/lang-cpp';
import {pythonLanguage} from '@codemirror/lang-python';
import {classHighlighter,highlightTree} from '@lezer/highlight';

const LIMIT=65536;
export function editorialLanguage(className='',source=''){
 const name=className.match(/language-([^\s]+)/)?.[1]?.toLowerCase();
 if(['cpp','c++','cpp17','cpp20','c','c99'].includes(name))return 'cpp17';
 if(['python','python3','py'].includes(name))return 'python3';
 return !name&&/^\s*#\s*include\s*[<"]/m.test(source)?'cpp17':null;
}

// Change only an unused increment of an integer declared by that for loop.
// Prefix increments in conditions, calls, literals and user code stay intact.
export function normalizeEditorialCode(source,language){
 if(language!=='cpp17'||source.length>LIMIT)return source;
 const tree=cppLanguage.parser.parse(source),cursor=tree.cursor(),edits=[];
 const collect=(node,names)=>{
  if(node.name==='UpdateExpression'){
   const value=source.slice(node.from,node.to),match=value.match(/^\+\+\s*([A-Za-z_]\w*)$/);
   if(match&&names.has(match[1]))edits.push({from:node.from,to:node.to,text:match[1]+'++'});
  }else if(['CommaExpression','ParenthesizedExpression'].includes(node.name)){
   for(let child=node.firstChild;child;child=child.nextSibling)collect(child,names);
  }
 };
 do{
  if(cursor.name!=='ForStatement')continue;
  const loop=cursor.node,declaration=loop.getChild('Declaration');if(!declaration)continue;
  const declarators=declaration.getChildren('InitDeclarator');
  const typeName=declarators.length&&source.slice(declaration.from,declarators[0].from).trim();
  const integer=typeName&&/^(?:(?:unsigned|signed|long|short)\s*)*(?:int|char|wchar_t|char16_t|char32_t)?$/.test(typeName);
  if(!integer)continue;
  const names=new Set(declarators.map(item=>item.getChild('Identifier')).filter(Boolean).map(item=>source.slice(item.from,item.to)));
  let previous=null;for(let child=loop.firstChild;child;child=child.nextSibling){if(child.name===')'){if(previous)collect(previous,names);break;}previous=child;}
 }while(cursor.next());
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
