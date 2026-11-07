// Original MathJax pages may leave HTML entities inside TeX, where Markdown
// does not decode them. Keep the source snapshot intact and normalize only the
// math node passed to KaTeX. A literal superscript prime has the same TeX meaning.
export default function remarkSourceMath(){
  return function transform(tree){
    function visit(node){
      if(node.type==='math'||node.type==='inlineMath'){
        node.value=node.value.replace(/&(?:amp;)?lt;/g,'<').replace(/&(?:amp;)?gt;/g,'>')
          .replace(/&nbsp;/g,' ').replace(/\^'/g,'^{\\prime}')
          .replace(/(?<!\\)\\([\[\]])/g,'$1').replace(/(^|[^\\])((?:\\\\)*)\\\s*$/,'$1$2')
          .replace(/\\(text|texttt|textrm)\{([^{}]*)\}/g,(_,macro,body)=>'\\'+macro+'{'+(body.includes('$')?body:body.replace(/(?<!\\)([_#&%])/g,'\\$1').replace(/(?<!\\)\^/g,'\\textasciicircum{}'))+'}')
          .replace(/^\s*#(\d+)\s*$/,'\\#$1');
        if(/^\s*[()&@.]+\s*$/.test(node.value))node.value=node.value.replace(/&/g,'\\&');
        // remark-math has already prepared its HAST text. Keep that actual
        // KaTeX input synchronized with the normalized MDAST value.
        const leaves=[];
        const collect=children=>{for(const child of children||[])if(child.type==='text')leaves.push(child);else collect(child.children);};
        collect(node.data?.hChildren);if(leaves.length===1)leaves[0].value=node.value;
      }
      for(const child of node.children||[])visit(child);
    }
    visit(tree);
  };
}
