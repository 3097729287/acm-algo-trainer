import { memo } from 'react';
import { Copy } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import ReadingImage, { readingUrlTransform } from './ReadingImage.jsx';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { normalizeMarkdown } from '@/lib/normalizeMarkdown.js';

export default memo(function SolutionMarkdown({ text, onCopy, images = {} }) {
  return <div className="markdown"><ReactMarkdown
    skipHtml
    urlTransform={readingUrlTransform}
    remarkPlugins={[remarkGfm, remarkMath]}
    rehypePlugins={[[rehypeKatex, { throwOnError: false, strict: 'ignore' }]]}
    components={{
      img: ({ node, ...props }) => <ReadingImage {...props} images={images} />,
      a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
      pre: props => <div className="code-block"><button className="copy-code" onClick={() => onCopy?.(props.children?.props?.children || '')}><Copy size={13} />复制</button><pre {...props} /></div>,
    }}
  >{normalizeMarkdown(text || '')}</ReactMarkdown></div>;
});
