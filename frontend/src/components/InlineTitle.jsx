import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { normalizeMarkdown } from '@/lib/normalizeMarkdown.js';
import './InlineTitle.css';

// Titles stay inline and noninteractive inside buttons, headings and list rows.
const inline = ({ children }) => <>{children}</>;
const components = {
  p: inline, h1: inline, h2: inline, h3: inline, h4: inline, h5: inline, h6: inline,
  blockquote: inline, ul: inline, ol: inline, li: inline, pre: inline, a: inline,
  img: ({ alt }) => alt || '',
  div: ({ node, ...props }) => <span {...props} />,
};
const remarkPlugins = [remarkMath];
const rehypePlugins = [[rehypeKatex, { throwOnError: false, strict: 'ignore', trust: false }]];

export default memo(function InlineTitle({ children }) {
  const text = String(children ?? '');
  // Ordinary names keep their literal punctuation and avoid Markdown parsing.
  if (!/\$|\\\(|\\\[/.test(text)) return text;
  return <span className="inline-title"><ReactMarkdown skipHtml remarkPlugins={remarkPlugins} rehypePlugins={rehypePlugins} components={components}>
    {normalizeMarkdown(text.replace(/\r?\n/g, ' '))}
  </ReactMarkdown></span>;
});
