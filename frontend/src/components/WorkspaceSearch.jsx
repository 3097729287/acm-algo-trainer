import {useEffect,useMemo,useState} from 'react';
import {BookOpen,ChevronRight,Code2,FileCode2,FlaskConical,LoaderCircle,NotebookTabs,Search,X} from 'lucide-react';
import {loadCatalogue} from '@/lib/catalogueCache.js';
import {LAB_CATALOG} from '@/lib/labCatalog.js';
import {searchWorkspace,workspaceSearchIndex} from '@/lib/workspaceSearch.js';
import InlineTitle from './InlineTitle.jsx';
import './WorkspaceSearch.css';
export function WorkspaceSearchInput({value,onChange}){
 return <div className="workspace-search-input"><Search size={17}/><input type="search" aria-label="统一搜索" value={value} onChange={event=>onChange(event.target.value)} onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();onChange('');}}}/>{value&&<button type="button" aria-label="清空搜索" onClick={()=>onChange('')}><X size={15}/></button>}</div>;
}
const ICONS={lecture:BookOpen,template:Code2,wiki:NotebookTabs,problem:FileCode2,lab:FlaskConical};
export default function WorkspaceSearchResults({query,api,owner,rows,onOpen,onClose}){
 const [catalogues,setCatalogues]=useState({}),[loading,setLoading]=useState(true),[failed,setFailed]=useState([]),[limit,setLimit]=useState(100);
 useEffect(()=>{let alive=true,pending=3;setCatalogues({});setLoading(true);setFailed([]);for(const path of ['lectures','templates','wiki'])void loadCatalogue(api,owner,path).then(value=>{if(alive)setCatalogues(previous=>({...previous,[path]:value}));}).catch(()=>{if(alive)setFailed(previous=>[...previous,path]);}).finally(()=>{if(alive&&--pending===0)setLoading(false);});return()=>{alive=false;};},[api,owner]);
 useEffect(()=>setLimit(100),[query]);
 const index=useMemo(()=>workspaceSearchIndex({rows,lectures:catalogues.lectures?.lectures||[],templates:catalogues.templates?.templates||[],wiki:catalogues.wiki?.articles||[],labs:LAB_CATALOG}),[rows,catalogues]);
 const matches=useMemo(()=>searchWorkspace(index,query),[index,query]);
 return <section className="workspace-search-results" aria-label="全局搜索结果"><header><span>搜索结果 <b>{matches.length}</b></span>{loading&&<LoaderCircle size={16} className="spin" aria-label="正在读取搜索目录"/>}<button type="button" className="icon-button" aria-label="关闭搜索结果" onClick={onClose}><X size={17}/></button></header><div className="workspace-search-list" role="list">{matches.slice(0,limit).map(item=>{const Icon=ICONS[item.kind];return <button type="button" role="listitem" className="workspace-search-row" key={item.key} aria-label={item.source+' '+item.title} title={item.title} onClick={()=>onOpen(item)}><Icon size={18}/><span className="workspace-search-title"><InlineTitle>{item.title}</InlineTitle></span><span className="workspace-search-context">{item.detail}</span><small>{item.source}</small><ChevronRight size={16}/></button>;})}{!matches.length&&!loading&&<p className="progress-muted">没有匹配内容。</p>}{failed.length>0&&<p className="progress-muted">部分目录暂时无法读取，已显示可用结果。</p>}{matches.length>limit&&<button type="button" className="workspace-search-more" onClick={()=>setLimit(previous=>previous+100)}>显示更多</button>}</div></section>;
}
