// Statement transcript cells use only <br> as a line separator. Turn that one
// inert element into Markdown breaks without allowing arbitrary raw HTML.
export default function remarkTableBreaks() {
  return tree => {
    function visit(node, inCell = false) {
      const cell = inCell || node.type === 'tableCell';
      if (!node.children) return;
      node.children = node.children.map(child => cell && child.type === 'html' && /^<br\s*\/?\s*>$/i.test(child.value.trim())
        ? { type: 'break' } : child);
      node.children.forEach(child => visit(child, cell));
    }
    visit(tree);
  };
}
