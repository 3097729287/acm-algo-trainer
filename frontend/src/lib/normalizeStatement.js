import {inputFormatMarkdown} from './inputFormat.js';
import {problemTitle} from './problemTitle.js';
// Presentation only: keep archive bytes and mathematical content unchanged.
// The fetch tool's comment banner is metadata already shown by the workbench.
export function normalizeStatement(markdown, samples = [], title = '') {
  let text = String(markdown || '').replaceAll('\r\n', '\n');
  const lines = text.split('\n');
  if (/^#{12,}\s*$/.test(lines[0] || '')) {
    const end = lines.findIndex((line, index) => index > 0 && /^#{12,}\s*$/.test(line));
    if (end > 0 && lines.slice(0, end).some(line => /^#\s*来源[:：]/.test(line))) {
      text = lines.slice(end + 1).join('\n').trimStart();
    }
  } else if (title && text.startsWith('# ' + title + '\n')) {
    const prefix = text.match(/^# [^\n]+\n\s*原题[:：]\s*https?:\/\/[^\n]+\n\s*/);
    if (prefix) text = text.slice(prefix[0].length);
  }
  text = text.replace(/^# ([^\n]+)$/m, (_, heading) => '# ' + problemTitle(heading));
  // Platform automation notices do not change the task's inputs, outputs or constraints.
  text = text.replace(/::anti-ai\[[^\]]*\]/g, '');
  // Promote legacy plain section labels without touching code or formulae.
  let fenced = null;
  text = text.split('\n').map(line => {
    const marker = line.match(/^\s*(`{3,}|~{3,})/);
    if (marker) { if (!fenced) fenced = marker[1][0]; else if (fenced === marker[1][0]) fenced = null; return line; }
    if (fenced) return line;
    const heading = line.match(/^\s*(题目描述|输入描述|输出描述|输入格式|输出格式|数据范围|约束条件)\s*[:：]?\s*$/);
    return heading ? '## ' + heading[1].replace('描述', heading[1] === '题目描述' ? '描述' : '格式') : line;
  }).join('\n');
  if (samples.length) {
    const banner = text.match(/\n={12,}\s*\n官方样例\s*\n={12,}\s*\n/);
    const legacy = text.match(/(?:^|\n)(?:#{1,4}\s*)?(?:示例|样例)\s*\d+\s*[:：]?\s*\n/);
    let sampleFence = null;
    const rawSamples = legacy && text.slice(legacy.index).split('\n').some(line => {
      const marker = line.match(/^\s*(`{3,}|~{3,})/);
      if (marker) { sampleFence = sampleFence ? null : marker[1][0]; return false; }
      return !sampleFence && /^\s*复制\s*$/.test(line);
    });
    let suffix = '';
    if (banner) text = text.slice(0, banner.index).trimEnd();
    else if (rawSamples) {
      const tail = text.slice(legacy.index);
      const notes = tail.match(/\n(?:#{1,4}\s*)?(?:备注|提示|Note|Notes|Hint|Hints)\s*[:：]?\s*\n/i);
      if (notes) suffix = tail.slice(notes.index);
      text = text.slice(0, legacy.index).trimEnd();
    }
    // Existing formatted samples remain intact. Otherwise display structured
    // official bytes rather than attempting to infer lost whitespace.
    const rendered = /(?:Sample Input|样例\s*输入|示例\s*输入|输入)\s*\d*\s*[:：]?\s*\n\s*`{3,}/i.test(text);
    if (banner || rawSamples || !rendered) text += '\n\n## 样例\n\n' + samples.map((sample, index) => {
      const values = [String(sample.input ?? ''), String(sample.output ?? '')].map(value => value.replace(/\r\n?/g, '\n'));
      const longest = Math.max(0, ...values.flatMap(value => [...value.matchAll(/`+/g)].map(match => match[0].length)));
      const delimiter = '`'.repeat(Math.max(3, longest + 1));
      const block = value => `${delimiter}text\n${value}${value.endsWith('\n') ? '' : '\n'}${delimiter}`;
      return `### 样例 ${index + 1}\n\n输入\n\n${block(values[0])}\n\n输出\n\n${block(values[1])}${sample.explanation ? '\n\n' + sample.explanation : ''}`;
    }).join('\n\n') + suffix;
  }
  return inputFormatMarkdown(text.trim());
}
