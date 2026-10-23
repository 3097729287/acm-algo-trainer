import { build } from 'vite';
import react from '@vitejs/plugin-react';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const frontend = fileURLToPath(new URL('../', import.meta.url)), repo = path.resolve(frontend, '..');
const output = path.resolve(process.argv[2] || path.join(repo, '../../版本/算法实验室体验版'));
const archive = path.join(path.dirname(output), '算法实验室-独立体验版.zip');
const result = await build({
  configFile: false, root: frontend, plugins: [react()], define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: { target: 'es2022', write: false, sourcemap: false, minify: true, cssCodeSplit: false,
    lib: { entry: path.join(frontend, 'standalone/main.jsx'), name: 'KnapsackApp', formats: ['iife'] },
  },
});
const chunks = (Array.isArray(result) ? result : [result]).flatMap(part => part.output);
const script = chunks.filter(part => part.type === 'chunk').map(part => part.code).join('\n');
const css = chunks.filter(part => part.type === 'asset' && part.fileName.endsWith('.css')).map(part => String(part.source)).join('\n');
if (!script || !css || chunks.some(part => part.type === 'chunk' && (part.imports.length || part.dynamicImports.length))) throw Error('Expected one self-contained app with inline styles.');
const html = `<!doctype html>\n<html lang="zh-CN" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark light"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>算法实验室 · 互动课</title><style>${css.replace(/<\/style/gi, '<\\/style')}</style></head><body><div id="root"></div><noscript>请启用浏览器 JavaScript 后打开互动课。</noscript><script>${script.replace(/<\/script/gi, '<\\/script')}</script></body></html>\n`;
const sourcePaths = [
  'frontend/standalone/main.jsx', 'frontend/standalone/KnapsackApp.jsx', 'frontend/standalone/labShell.css',
  'frontend/src/pages/LearningPathsPage.jsx', 'frontend/src/components/PageSearch.jsx',
  ...(await readdir(path.join(frontend, 'src/pages/algorithm-lab'))).filter(name => /\.(jsx?|css)$/.test(name)).map(name => `frontend/src/pages/algorithm-lab/${name}`),
  'frontend/scripts/build-algorithm-lab.mjs',
];
const sha256 = content => createHash('sha256').update(content).digest('hex');
const sources = await Promise.all(sourcePaths.map(async file => ({ path: file, sha256: sha256(await readFile(path.join(repo, file))) })));
let sourceBaseline = 'unavailable';
try { sourceBaseline = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim(); } catch { /* A source export may have no .git directory. */ }
const VERSION = '0.5.0';
const info = { product: '算法实验室 · 独立互动课', version: VERSION, courses: ['前缀和与差分', '双指针算法', '背包 DP'], lessons: 21, guidedProblems: 15, status: 'standalone preview; not a TB release', builtAt: new Date().toISOString(), sourceBaseline, sourceIdentity: 'SHA-256 manifest of the working sources below', sources, files: { '开始体验.html': sha256(html) } };
const licenses = await Promise.all(['react', 'react-dom', 'lucide-react'].map(async name => `${name}\n${await readFile(path.join(frontend, 'node_modules', name, 'LICENSE'), 'utf8')}`));
const files = {
  '开始体验.html': html,
  '使用说明.txt': `算法实验室 · 独立互动课 ${VERSION}\r\n\r\n解压后双击“开始体验.html”，用 Edge 或 Chrome 打开，无需安装、联网或启动服务器。\r\n目录有“前缀和与差分”“双指针算法”“背包 DP”，各七节互动课与五道精选跟做题。\r\n可以改数据、单步推演、移动边界、预测、修错，再独立实现 C++。方向键翻页；输入框内方向键仍供编辑使用。\r\n每个专题独立保存进度，关闭后可继续；旧背包进度沿用。换浏览器、文件位置或清空浏览器数据后，原进度可能无法继续。\r\n“打开原题”需要联网；完整 C++ 程序请在自己的编译器运行。课堂核对不产生正式 AC。\r\n\r\n这是独立体验包，不是 TB 主程序更新包。主应用源码已接入；是否已经打包安装请看本机“当前更新”。\r\n`,
  'README.en.txt': `Algorithm Lab ${VERSION}\r\n\r\nExtract and open 开始体验.html in Edge or Chrome. No installation, network or server required.\r\nThree independent courses: prefix sums and difference arrays, two pointers, knapsack DP. Each has seven lessons and five guided problems.\r\nChange inputs, step through executions, move boundaries, predict results and repair counterexamples. Arrow keys navigate lessons outside editable controls.\r\nProgress stays in this browser. Existing knapsack progress is preserved. Changing browser or file location, or clearing browser data, may prevent restoring progress.\r\nOriginal-problem links require internet. Compile complete C++ programs in your own environment. Classroom checks do not count as official accepted submissions.\r\nThis standalone preview is separate from the TB desktop release.\r\n`,
  'LICENSES.txt': licenses.join('\n\n'),
  'BUILD-INFO.json': JSON.stringify(info, null, 2) + '\n',
};
await mkdir(output, { recursive: true });
for (const [name, content] of Object.entries(files)) await writeFile(path.join(output, name), content, 'utf8');
if (process.platform !== 'win32') throw Error('ZIP packaging currently uses Windows PowerShell; the generated HTML is portable.');
execFileSync('powershell.exe', ['-NoProfile', '-Command', "$labFiles = @('开始体验.html','使用说明.txt','README.en.txt','LICENSES.txt','BUILD-INFO.json') | ForEach-Object { Join-Path $env:TB_LAB_PACKAGE_DIR $_ }; Compress-Archive -LiteralPath $labFiles -DestinationPath $env:TB_LAB_PACKAGE_ZIP -Force"], {
  env: { ...process.env, TB_LAB_PACKAGE_DIR: output, TB_LAB_PACKAGE_ZIP: archive }, windowsHide: true, stdio: 'pipe',
});
console.log(JSON.stringify({ output, archive, htmlBytes: Buffer.byteLength(html), zipBytes: (await readFile(archive)).length, htmlSha256: sha256(html) }, null, 2));
