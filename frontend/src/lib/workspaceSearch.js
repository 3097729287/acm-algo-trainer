import {buildLearningIndex} from './learningBrowser.js';
import {normalizeProblemCode} from './problemSearchCodes.js';
export const SEARCH_SOURCES={lecture:'从零讲',template:'模板',wiki:'维基百科',problem:'单题',lab:'实验室'};
const plain=value=>String(value||'').normalize('NFKC').toLocaleLowerCase().replace(/\s+/g,' ').trim();
export function workspaceSearchIndex(catalogues){const details=new Map((catalogues.rows||[]).map(item=>['problem:'+item.id,[item.platform,item.contest||item.contestName,item.problem||item.code].filter(Boolean).join(' · ')]));return buildLearningIndex(catalogues).map(item=>({...item,source:SEARCH_SOURCES[item.kind],detail:details.get(item.key)||'',normalizedCodes:(item.problemCodes||[]).filter(code=>/\d/.test(code.normalize('NFKC'))).map(normalizeProblemCode),normalizedTitle:plain(item.title),normalizedSearch:plain(item.search)}));}
export function searchWorkspace(index,query){
 const needle=plain(query),words=needle.split(' ').filter(Boolean);if(!words.length)return [];
 const code=normalizeProblemCode(needle),exact=item=>item.normalizedCodes?.includes(code),order=['lecture','template','wiki','lab','problem'];
 return index.filter(item=>exact(item)||words.every(word=>item.normalizedSearch.includes(word))).map(item=>({...item,score:exact(item)?-1:item.normalizedTitle===needle?0:item.normalizedTitle.startsWith(needle)?1:item.normalizedTitle.includes(needle)?2:3})).sort((a,b)=>a.score-b.score||order.indexOf(a.kind)-order.indexOf(b.kind)||a.title.localeCompare(b.title,'zh-CN')||a.id.localeCompare(b.id));
}
