import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { normalizeMarkdown } from '@/lib/normalizeMarkdown.js';

// Loaded only for a title containing math. Titles remain noninteractive.
const inline = ({ children }) => <>{children}</>;
const components = {
  p: inline, h1: inline, h2: inline, h3: inline, h4: inline, h5: inline, h6: inline,
  blockquote: inline, ul: inline, ol: inline, li: inline, pre: inline, a: inline,
  img: ({ alt }) => alt || '',
  div: ({ node, ...props }) => <span {...props} />,
};
const remarkPlugins = [remarkMath];
const rehypePlugins = [[rehypeKatex, { throwOnError: false, strict: 'ignore', trust: false }]];
export default function MathTitle({ text }) {
  return <span className="inline-title"><ReactMarkdown skipHtml remarkPlugins={remarkPlugins} rehypePlugins={rehypePlugins} components={components}>
    {normalizeMarkdown(text.replace(/\r?\n/g, ' '))}
  </ReactMarkdown></span>;
}
