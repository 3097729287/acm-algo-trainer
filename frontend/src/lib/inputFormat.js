// Repair the old AtCoder <pre><var> conversion only in input specifications.
// Sample bytes and actual source-code fences must never be typeset as math.
export function inputFormatMarkdown(markdown) {
  let section = '';
  return String(markdown).replace(/^(#{1,6})\s+([^\n]+)$|^(`{3,}|~{3,})([^\n]*)\n([\s\S]*?)\n\3[ \t]*$/gm,
    (whole, heading, title, fence, language, body) => {
      if (heading) {section=title.trim();return whole;}
      const typed=language.trim()==='input-format';
      const legacy=/^(?:Input|Input Format|入力|输入格式|输入描述)$/i.test(section)
        && /^(?:text)?$/.test(language.trim()) && /[_^]|\\(?:ldots|cdots|dots|vdots)/.test(body)
        && body.split('\n').every(line=>/^[\w\s\\{},.^_+()\[\]-]*$/.test(line))
        && !/\b(?:include|return|while|for|printf|cin|cout|int|def|print)\b|[;=<>]/.test(body);
      if (!typed&&!legacy)return whole;
      const lines=body.split('\n').map(line=>typed?line:line.trim().split(/\s+/).filter(Boolean).map(token=>`$${token}$`).join(' '));
      return lines.map(line=>line.trim()?`> ${line}`:'>').join('\n>\n');
    });
}
