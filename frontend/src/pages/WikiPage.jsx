import {useEffect,useRef,useState} from 'react';
import {ArrowLeft,BookOpen,ChevronRight,ExternalLink,Info,LoaderCircle,Search,X} from 'lucide-react';
import PageSearch from '@/components/PageSearch.jsx';
import './WikiPage.css';

export default function WikiPage({api,initialArticle,onOpenArticle,visit,embedded=false}){
 const [query,setQuery]=useState(''),[catalogue,setCatalogue]=useState([]),[article,setArticle]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const frame=useRef(null),sourceDialog=useRef(null),sequence=useRef(0),all=useRef([]),hash=useRef('');
 useEffect(()=>{let live=true;const timer=setTimeout(()=>{setLoading(true);api('wiki?q='+encodeURIComponent(query)).then(value=>{if(live){setCatalogue(value.articles);if(!query)all.current=value.articles;setError('');}}).catch(issue=>{if(live)setError(issue.message);}).finally(()=>{if(live)setLoading(false);});},150);return()=>{live=false;clearTimeout(timer);};},[api,query]);
 useEffect(()=>{if(initialArticle)void open(initialArticle,visit?.anchor||'');return()=>{sequence.current++;};},[initialArticle,api]);
 async function open(id,anchor=''){
  const seq=++sequence.current;setLoading(true);setError('');
  try{const value=await api('wiki?id='+encodeURIComponent(id));if(seq===sequence.current){hash.current=anchor;
   const doc=new DOMParser().parseFromString(value.article.html,'text/html'),source=[...doc.querySelectorAll('blockquote,footer,.md-source-file')].filter(node=>node.textContent.includes('本页面贡献者')&&node.textContent.includes('CC BY-SA')&&node.textContent.includes('SATA'));
   const sourceHtml=source.map(node=>node.outerHTML).join('');source.forEach(node=>{if(node.previousElementSibling?.tagName==='HR')node.previousElementSibling.remove();node.remove();});
   setArticle({...value.article,contentHtml:doc.body.innerHTML,sourceHtml});}}
  catch(issue){if(seq===sequence.current)setError(issue.message);}
  finally{if(seq===sequence.current)setLoading(false);}
 }
 function loaded(){
  const doc=frame.current?.contentDocument;if(!doc)return;
  if(visit&&doc.scrollingElement){doc.scrollingElement.scrollTop=visit.wikiScroll||0;doc.addEventListener('scroll',()=>{visit.wikiScroll=doc.scrollingElement.scrollTop;},{passive:true});}
  if(hash.current){doc.getElementById(decodeURIComponent(hash.current.slice(1)))?.scrollIntoView();hash.current='';}
  doc.addEventListener('click',event=>{
   const link=event.target.closest('a[href]');if(!link)return;
   const url=new URL(link.href),id=url.pathname.replace(/^\/|\/$/g,'');
   if(url.origin==='https://oi-wiki.org'&&all.current.some(item=>item.id===id)){
    event.preventDefault();if(id===article?.id&&url.hash)doc.getElementById(decodeURIComponent(url.hash.slice(1)))?.scrollIntoView();else if(onOpenArticle)onOpenArticle({id,title:all.current.find(item=>item.id===id)?.title,visit:{anchor:url.hash}});else void open(id,url.hash);
   }
  });
 }
 const root=getComputedStyle(document.documentElement),color=root.getPropertyValue('--text')||'#ddd',muted=root.getPropertyValue('--muted')||'#999',accent=root.getPropertyValue('--accent')||'#9b8afb',line=root.getPropertyValue('--line')||'#555';
 const documentHtml=html=>`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><style>
 :root{color-scheme:${document.documentElement.dataset.theme==='light'?'light':'dark'}}*{box-sizing:border-box}body{margin:0;padding:24px clamp(16px,4vw,56px) 60px;color:${color};font:16px/1.85 system-ui,sans-serif;overflow-wrap:anywhere}article{max-width:980px;margin:auto}a{color:${accent}}h1,h2,h3{line-height:1.5}h1{font-size:1.8em}h2{font-size:1.4em;margin-top:1.8em}h3{font-size:1.15em}pre{overflow:auto;padding:16px;border:1px solid ${line};border-radius:8px;line-height:1.55;tab-size:4;white-space:pre}code{font: .87em/1.55 Consolas,monospace}p code,li code{color:${accent}}img{max-width:100%;height:auto;display:block;margin:16px auto}table{border-collapse:collapse;display:block;max-width:100%;overflow:auto}th,td{border:1px solid ${line};padding:6px 10px}pre table{display:table}pre td{border:0;padding:0}blockquote,.admonition,details{border-left:3px solid ${accent};margin:16px 0;padding:4px 18px}summary{cursor:pointer}math{font-family:math;font-size:1.1em}math[display=block]{overflow:auto;margin:18px 0}annotation{display:none}.md-source-file{font-size:.8em;color:${muted};border-top:1px solid ${line};margin-top:40px}.tabbed-labels{display:none}.tabbed-content{display:block}.tabbed-block{margin-block:16px}.tabbed-block:before{content:attr(data-language);font-weight:bold}.highlight .k,.highlight .kt{color:${accent}}.highlight .c1,.highlight .cm{color:${muted}}
 </style></head><body>${html}</body></html>`;
 const src=article?documentHtml(article.contentHtml):'';
 return <section className="list-page wiki-page" aria-label="维基百科">
  <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索维基百科" value={query} onChange={event=>{sequence.current++;setArticle(null);setQuery(event.target.value);}}/></label></PageSearch>
  {article?<><header className="wiki-reader-toolbar"><button type="button" className="icon-button" aria-label="返回维基目录" onClick={()=>{sequence.current++;setArticle(null);}}><ArrowLeft size={18}/></button><strong>{article.title}</strong>{article.sourceHtml&&<button type="button" className="icon-button" aria-label="来源与许可" title="来源与许可" onClick={()=>sourceDialog.current?.showModal()}><Info size={17}/></button>}<a className="icon-button" href={article.url} target="_blank" rel="noreferrer" aria-label="OI Wiki 原文"><ExternalLink size={17}/></a></header><iframe ref={frame} onLoad={loaded} title={article.title} className="wiki-reader" sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox" srcDoc={src}/>{article.sourceHtml&&<dialog ref={sourceDialog} className="wiki-source-dialog" aria-label="来源与许可"><header><strong>来源与许可</strong><button type="button" className="icon-button" aria-label="关闭来源与许可" onClick={()=>sourceDialog.current?.close()}><X size={17}/></button></header><iframe title="OI Wiki 来源与许可" sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox" srcDoc={documentHtml(article.sourceHtml)}/></dialog>}</>:<div className="wiki-catalogue">{[...new Set(catalogue.map(item=>item.category))].map(category=><section key={category}><h3>{category}</h3>{catalogue.filter(item=>item.category===category).map(item=><button type="button" className="wiki-entry" key={item.id} onClick={()=>onOpenArticle?onOpenArticle(item):open(item.id)}><BookOpen size={17}/><span>{item.title}</span><ChevronRight size={16}/></button>)}</section>)}{!loading&&!catalogue.length&&<div className="progress-empty"><Search size={24}/><span>没有匹配的内容</span></div>}</div>}
  {loading&&<span className="wiki-loading" role="status" aria-label="正在读取维基百科"><LoaderCircle className="progress-spin" size={19}/></span>}{error&&<p className="connection-error" role="alert">{error}</p>}
 </section>;
}
