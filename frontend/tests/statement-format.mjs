import assert from 'node:assert/strict';
import { normalizeStatement } from '../src/lib/normalizeStatement.js';

const samples=[{input:'5 3\n1 2 3 4 5\n',output:'2\n',explanation:'计数器最后为 $2$。'}];
const legacy='小月的增减\n\n题目描述\n\n原始正文。\n\n输入描述:\n\n两行数据。\n\n示例1\n\n输入\n\n复制\n\n5 3 1 2 3 4 5\n\n输出\n\n复制\n\n2\n\n提示\n\n保留提示。';
const result=normalizeStatement(legacy,samples,'小月的增减');
assert.ok(result.includes('## 题目描述'));
assert.ok(result.includes('## 输入格式'));
assert.ok(result.includes('```text\n5 3\n1 2 3 4 5\n```'));
assert.ok(!result.includes('复制'));
assert.ok(result.includes('保留提示。'));
assert.equal(normalizeStatement(result,samples,'小月的增减'),result,'Normalization is idempotent');
const code='```cpp\n输入描述:\nconst char *s="复制";\n```';
assert.equal(normalizeStatement(code),code);
const formatted='## Sample Input 1\n\n```text\n复制\n```\n\n## Sample Output 1\n\n```text\n2\n```';
assert.equal(normalizeStatement(formatted,samples),formatted,'Formatted English examples are not duplicated or rewritten');
assert.equal(normalizeStatement('$a_i < n$\n\n- One\n- Two'),'$a_i < n$\n\n- One\n- Two');
assert.ok(normalizeStatement('## Description\n\nRead numbers.',[{input:'a\n```\nb\n',output:''}]).includes('````text\na\n```\nb\n````'));
console.log('Statement formatting: official sample newlines, notes, headings, code/math, safe fences and idempotence passed.');
