// Only the requested statement DOM is returned. Login forms, scripts, session
// state and unrelated browser content never enter the loopback transport.
function tbConnectedRead(identity){
 const result={url:location.origin+location.pathname,ready:document.readyState,identity};
 if(document.readyState==='loading')return result;
 if(/just a moment|checking your browser|人机验证|安全验证/i.test(document.title))return {...result,state:'verification'};
 if(identity?.state!=='logged_in')return {...result,state:'login'};
 const nodes=[...document.querySelectorAll('.subject-item-title,.subject-describe,.question-oi')];
 if(!nodes.length)return {...result,html:(document.body?.innerText||'').slice(0,4000)};
 const html=nodes.filter(node=>!nodes.some(parent=>parent!==node&&parent.contains(node))).map(node=>{
  const copy=node.cloneNode(true);
  for(const remove of copy.querySelectorAll('script,style,form,input,button,iframe,object,embed'))remove.remove();
  for(const element of [copy,...copy.querySelectorAll('*')])for(const attribute of [...element.attributes]){
   if(/^on/i.test(attribute.name)||!['class','src','href','alt','title','colspan','rowspan'].includes(attribute.name))element.removeAttribute(attribute.name);
   else if(['src','href'].includes(attribute.name)&&!/^https?:|^\/|^#|^data:image\//i.test(attribute.value))element.removeAttribute(attribute.name);
  }
  return copy.outerHTML;
 }).join('\n');
 if(new TextEncoder().encode(html).length>4000000)throw Error('Statement exceeds limit');
 return {...result,html};
}
