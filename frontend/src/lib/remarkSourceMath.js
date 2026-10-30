// Original MathJax pages may leave HTML entities inside TeX, where Markdown
// does not decode them. Keep the source snapshot intact and normalize only the
// math node passed to KaTeX. A literal superscript prime has the same TeX meaning.
export default function remarkSourceMath(){
  return function transform(tree){
    function visit(node){
      if(node.type==='math'||node.type==='inlineMath'){
        node.value=node.value.replace(/&(?:amp;)?lt;/g,'<').replace(/&(?:amp;)?gt;/g,'>')
          .replace(/&nbsp;/g,' ').replace(/\^'/g,'^{\\prime}');
      }
      for(const child of node.children||[])visit(child);
    }
    visit(tree);
  };
}
