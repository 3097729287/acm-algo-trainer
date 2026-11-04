import { memo, useMemo } from 'react';
import { Copy } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import ReadingImage, { readingUrlTransform } from './ReadingImage.jsx';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { normalizeMarkdown } from '@/lib/normalizeMarkdown.js';

const EMPTY_IMAGES=Object.freeze({});

export default memo(function SolutionMarkdown({ text, onCopy, images = EMPTY_IMAGES,onOpenWiki }) {
  const components=useMemo(()=>({
    img: ({ node, ...props }) => <ReadingImage {...props} images={images} />,
    a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer" onClick={event=>{if(!onOpenWiki||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;try{const url=new URL(props.href);if(url.origin==='https://oi-wiki.org'){event.preventDefault();onOpenWiki(url.pathname.replace(/^\/|\/$/g,''),url.hash);}}catch{}}}/>,
    pre: props => <div className="code-block"><button className="copy-code" onClick={() => onCopy?.(props.children?.props?.children || '')}><Copy size={13} />复制</button><pre {...props} /></div>,
  }),[images,onCopy,onOpenWiki]);
  return <div className="markdown"><ReactMarkdown
    skipHtml
    urlTransform={readingUrlTransform}
    remarkPlugins={[remarkGfm, remarkMath]}
    rehypePlugins={[[rehypeKatex, { throwOnError: false, strict: 'ignore' }]]}
    components={components}
  >{normalizeMarkdown(text || '')}</ReactMarkdown></div>;
});
