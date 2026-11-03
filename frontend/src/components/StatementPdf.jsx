import {useEffect, useRef, useState} from 'react';
import {Download,LoaderCircle} from 'lucide-react';
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import './StatementPdf.css';

function PdfPage({document,pdfjs,number,total,width,zoom,aspect,title,onError}){
  const element=useRef(null),canvas=useRef(null),text=useRef(null);
  const [visible,setVisible]=useState(number===1),[page,setPage]=useState(null),[ready,setReady]=useState(false);
  useEffect(()=>{
    const observer=new IntersectionObserver(entries=>setVisible(entries[0].isIntersecting),{
      root:element.current.closest('.wb-statement'),rootMargin:'800px 0px'});
    observer.observe(element.current);return()=>observer.disconnect();
  },[]);
  useEffect(()=>{
    if(!visible||page)return;
    let active=true;document.getPage(number).then(value=>{if(active)setPage(value);},()=>{if(active)onError(true);});
    return()=>{active=false;};
  },[document,number,visible,page,onError]);
  const available=Math.max(1,width-24)*zoom;
  const viewport=page?.getViewport({scale:available/page.getViewport({scale:1}).width});
  useEffect(()=>{
    setReady(false);
    if(!visible||!viewport||!canvas.current||!text.current)return;
    let active=true,render,layer;
    const target=canvas.current,container=text.current;
    const ratio=Math.min(window.devicePixelRatio||1,2,Math.sqrt(8_000_000/(viewport.width*viewport.height)));
    target.width=Math.max(1,Math.floor(viewport.width*ratio));target.height=Math.max(1,Math.floor(viewport.height*ratio));
    render=page.render({canvasContext:target.getContext('2d'),viewport,transform:[ratio,0,0,ratio,0,0],background:'rgb(255,255,255)'});
    layer=new pdfjs.TextLayer({textContentSource:page.streamTextContent(),container,viewport});
    Promise.all([render.promise,layer.render()]).then(()=>{if(active)setReady(true);},error=>{
      if(active&&error?.name!=='RenderingCancelledException'&&error?.name!=='AbortException')onError(true);
    });
    return()=>{active=false;render.cancel();layer.cancel();container.replaceChildren();target.width=target.height=0;};
  },[page,pdfjs,visible,viewport?.width,viewport?.height,onError]);
  const scale=viewport?.scale||1;
  return <div ref={element} className="wb-pdf-page" data-page={number} data-ready={ready?'true':'false'}
    style={{width:available,height:viewport?.height||available*aspect,'--scale-factor':scale,'--total-scale-factor':scale*(page?.userUnit||1)}}>
    <canvas ref={canvas} role="img" aria-label={`${title||'题面内容'} · ${number}/${total}`} />
    <div ref={text} className="wb-pdf-text-layer" />
  </div>;
}

export default function StatementPdf({pdf,title,fontSize=16}){
  const element=useRef(null),initialFont=useRef(fontSize);
  const [width,setWidth]=useState(0),[content,setContent]=useState(null),[source,setSource]=useState(''),[error,setError]=useState(false);
  const data=pdf?.data||'';
  useEffect(()=>{
    const observer=new ResizeObserver(entries=>setWidth(entries[0].contentRect.width));
    observer.observe(element.current);return()=>observer.disconnect();
  },[]);
  useEffect(()=>{
    let active=true,task,url;
    setContent(null);setSource('');setError(false);
    (async()=>{
      try{
        if(!/^data:application\/pdf;base64,[a-z\d+/=\s]+$/i.test(data))throw new Error('Invalid PDF');
        const bytes=Uint8Array.from(atob(data.split(',')[1]),char=>char.charCodeAt(0));
        url=URL.createObjectURL(new Blob([bytes],{type:'application/pdf'}));
        if(active)setSource(url);
        const pdfjs=await import('pdfjs-dist/build/pdf.mjs');if(!active)return;
        pdfjs.GlobalWorkerOptions.workerSrc=workerUrl;
        const base=new URL(`${import.meta.env.BASE_URL}pdfjs/${pdfjs.version}/`,window.location.href).href;
        task=pdfjs.getDocument({data:bytes,cMapUrl:base+'cmaps/',standardFontDataUrl:base+'standard_fonts/',
          wasmUrl:base+'wasm/',iccUrl:base+'iccs/',disableWorkerRendering:true,canvasMaxAreaInBytes:32_000_000,enableXfa:false});
        const document=await task.promise;if(!active)return;
        if(!document.numPages||document.numPages>32)throw new Error('Unsupported page count');
        const first=await document.getPage(1),viewport=first.getViewport({scale:1});
        if(active)setContent({document,pdfjs,count:document.numPages,aspect:viewport.height/viewport.width});
      }catch{if(active)setError(true);}
    })();
    return()=>{active=false;task?.destroy().catch(()=>{});if(url)URL.revokeObjectURL(url);};
  },[data]);
  return <div ref={element} className="wb-statement-pdf" role="document" aria-label={title||'题面内容'}>
    {source&&<div className="wb-pdf-actions"><a href={source} download={pdf.fileName||'statement.pdf'} className="wb-icon-button" title="下载 PDF" aria-label="下载 PDF"><Download size={16}/></a></div>}
    {error?<div className="wb-empty" role="alert">题面暂时未能加载</div>:!content?<div className="wb-empty" role="status"><LoaderCircle size={22} className="wb-spinner"/>正在载入题面</div>:
      width>0&&Array.from({length:content.count},(_,index)=><PdfPage key={index} {...content} number={index+1} total={content.count} width={width} zoom={fontSize/initialFont.current} title={title} onError={setError}/>)}
  </div>;
}
