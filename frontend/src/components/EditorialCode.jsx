import {memo,useEffect,useMemo,useState} from 'react';
import {Copy} from 'lucide-react';
import {editorialLanguage,normalizeEditorialCode,editorialTokens,formatEditorialCode} from '@/lib/editorialCode.js';
import './EditorialCode.css';

export default memo(function EditorialCode({source='',className='',onCopy,api,problemId}){
 const language=editorialLanguage(className,source);
 const normalized=useMemo(()=>normalizeEditorialCode(source,language),[source,language]);
 const [formatted,setFormatted]=useState(null);
 const code=formatted?.source===normalized&&formatted.language===language?formatted.code:normalized;
 useEffect(()=>{
  if(!api||!problemId||!language||new TextEncoder().encode(normalized).length>65536)return;
  let active=true;
  formatEditorialCode(api,problemId,normalized,language).then(value=>{if(active)setFormatted({source:normalized,language,code:value});}).catch(()=>{/* The original reference remains readable. */});
  return()=>{active=false;};
 },[api,problemId,normalized,language]);
 const tokens=useMemo(()=>editorialTokens(code,language),[code,language]);
 return <div className="code-block editorial-code"><button type="button" className="copy-code" onClick={()=>onCopy?.(code)}><Copy size={13}/>复制</button><pre><code className={className}>{tokens.map((part,index)=>part.classes?<span key={index} className={part.classes}>{part.text}</span>:part.text)}</code></pre></div>;
});
