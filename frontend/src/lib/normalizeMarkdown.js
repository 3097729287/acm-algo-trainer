// Adapt platform/LaTeX and legacy Typora formula boundaries while displaying.
// Code, escaped dollars, and unmatched delimiters remain unchanged.
function escaped(text,index){let slashes=0;for(let i=index-1;i>=0&&text[i]==='\\';i--)slashes++;return slashes%2===1}

function closing(text, marker, start, singleLine=false){
  for(let index=start;index<text.length;index++){
    if(singleLine&&text[index]==='\n')return -1;
    if(text.startsWith(marker,index)&&!escaped(text,index))return index;
    if(text[index]==='`'){
      let end=index;while(text[end]==='`')end++;
      const delimiter=text.slice(index,end),finish=text.indexOf(delimiter,end);
      if(finish>=0)index=finish+delimiter.length-1;
    }
  }
  return -1;
}

function display(out, body, suffix){
  const tail=out.slice(out.lastIndexOf('\n')+1);
  // List-contained display math needs the closing delimiter at the same
  // indentation as its opener. A column-zero close makes Markdown consume
  // later prose as another equation.
  const indent=tail.trim()?'':tail;
  if(tail.trim())out+='\n\n';else if(indent)out=out.slice(0,-indent.length);
  const lines=body.replace(/^(?:[ \t]*\n)+|(?:\n[ \t]*)+$/g,'').split('\n').map(line=>line.startsWith(indent)?line:indent+line);
  out+=indent+'$$\n'+lines.join('\n')+'\n'+indent+'$$';
  if(suffix.split('\n',1)[0].trim())out+='\n\n';
  return out;
}

function inlineFormula(out, body, suffix){
  if(/\\tag\s*\{|\\begin\{(?:equation\*?|align\*?)\}/.test(body))return display(out,body,suffix);
  if(out.endsWith('$')&&!escaped(out,out.length-1))out+=' ';
  out+='$'+body+'$';
  if(suffix.startsWith('$')||suffix.startsWith('\\('))out+=' ';
  return out;
}

function prose(text){
  let out='',i=0,inline=false;
  while(i<text.length){
    if(text[i]==='`'){
      let end=i;while(text[end]==='`')end++;
      const marker=text.slice(i,end),close=text.indexOf(marker,end);
      if(close>=0){out+=text.slice(i,close+marker.length);i=close+marker.length;continue}
    }
    if(!inline&&text[i]==='\\'&&!escaped(text,i)&&['(', '['].includes(text[i+1])){
      const block=text[i+1]==='[',end=i+2;
      const close=closing(text,block?'\\]':'\\)',end,!block);
      if(close>=0){
        const body=text.slice(end,close);
        // Imported prose uses Markdown-escaped brackets for optional syntax
        // such as \[_object_\] and intervals containing their own $...$ math.
        if(block&&(body.includes('$')||/(?:\\?_)[A-Za-z][A-Za-z0-9]*_/.test(body))){out+=text.slice(i,end);i=end;continue;}
        out=block?display(out,body,text.slice(close+2)):inlineFormula(out,body,text.slice(close+2));
        i=close+2;continue;
      }
    }
    if(text[i]!=='$'||escaped(text,i)){out+=text[i++];continue}
    let end=i;while(text[end]==='$')end++;
    const count=end-i;
    if(count===6&&!inline){
      const close=closing(text,'$$$$$$',end),body=close>=0?text.slice(end,close):'';
      if(close>=0&&!body.includes('$')&&/\\[A-Za-z]+/.test(body)){
        out=display(out,body,text.slice(close+6));i=close+6;continue;
      }
    }
    if(count===3&&!inline){
      // Codeforces uses $$$...$$$ for inline math, including adjacent runs.
      const close=closing(text,'$$$',end);
      if(close>=0){
        const body=text.slice(end,close);
        out=body.includes('\n')?display(out,body,text.slice(close+3)):inlineFormula(out,body,text.slice(close+3));
        i=close+3;continue;
      }
    }
    if(count===1){
      if(!inline){
        const close=closing(text,'$',end),body=close>=0?text.slice(end,close):'';
        if(close>=0&&!body.includes('$')&&/\\tag\s*\{|\\begin\{(?:equation\*?|align\*?)\}/.test(body)){
          out=display(out,body,text.slice(close+1));i=close+1;continue;
        }
      }
      // Avoid interpreting an unmatched currency/dollar as an inline opener.
      const lineEnd=text.indexOf('\n',end),limit=lineEnd<0?text.length:lineEnd;
      let closes=false;
      for(let j=end;j<limit;j++)if(text[j]==='$'&&!escaped(text,j)){closes=true;break}
      if(inline||closes)inline=!inline;
      out+='$';i=end;continue;
    }
    if(count!==2){out+=text.slice(i,end);i=end;continue}
    if(inline){
      // Adjacent inline formulas: $a$$b$ -> $a$ $b$.
      out+='$ $';i=end;continue;
    }
    let close=-1;
    for(let j=end;j<text.length-1;j++){
      if(text[j]==='`'){
        let k=j;while(text[k]==='`')k++;
        const marker=text.slice(j,k),finish=text.indexOf(marker,k);
        if(finish>=0){j=finish+marker.length-1;continue}
      }
      if(text.slice(j,j+2)==='$$'&&!escaped(text,j)&&text[j+2]!=='$') {close=j;break}
    }
    if(close<0){out+='$$';i=end;continue}
    const body=text.slice(end,close);
    // Markdown treats same-line double dollars as inline math. Native pages
    // use them for display equations, including tagged equations.
    out=display(out,body,text.slice(close+2));
    i=close+2;
  }
  return out;
}

export function normalizeMarkdown(text=''){
  const lines=String(text).split(/(?<=\n)/),parts=[];
  let pending='',fence=null;
  const flush=()=>{if(pending){parts.push(prose(pending));pending=''}};
  for(const line of lines){
    const match=line.match(/^ {0,3}(`{3,}|~{3,})/);
    if(fence){
      parts.push(line);
      if(match&&match[1][0]===fence.character&&match[1].length>=fence.length&&line.slice(match[0].length).trim()==='')fence=null;
    }else if(match){flush();fence={character:match[1][0],length:match[1].length};parts.push(line)}
    else pending+=line;
  }
  flush();
  return parts.join('');
}
