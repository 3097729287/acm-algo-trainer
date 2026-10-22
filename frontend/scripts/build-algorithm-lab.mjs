import { build } from 'vite';
import react from '@vitejs/plugin-react';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const frontend = fileURLToPath(new URL('../', import.meta.url)), repo = path.resolve(frontend, '..');
const output = path.resolve(process.argv[2] || path.join(repo, '../../版本/算法实验室体验版'));
const archive = path.join(path.dirname(output), '背包DP-独立体验版.zip');
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
const html = `<!doctype html>\n<html lang="zh-CN" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark light"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>背包 DP · 互动课</title><style>${css.replace(/<\/style/gi, '<\\/style')}</style></head><body><div id="root"></div><noscript>请启用浏览器 JavaScript 后打开互动课。</noscript><script>${script.replace(/<\/script/gi, '<\\/script')}</script></body></html>\n`;
const sourcePaths = [
  'frontend/standalone/main.jsx', 'frontend/standalone/KnapsackApp.jsx', 'frontend/standalone/labShell.css',
  ...['KnapsackCourse.jsx', 'KnapsackLab.jsx', 'PackingExperiment.jsx', 'StateExperiment.jsx', 'KnapsackFoundations.jsx', 'KnapsackExperiments.jsx', 'KnapsackChallenges.jsx', 'GuidedWorkshop.jsx', 'guidedProblems.js', 'LabParts.jsx', 'knapsackModel.js', 'knapsackCourse.js', 'algorithmLab.css'].map(name => `frontend/src/pages/algorithm-lab/${name}`),
  'frontend/scripts/build-algorithm-lab.mjs',
];
const sha256 = content => createHash('sha256').update(content).digest('hex');
const sources = await Promise.all(sourcePaths.map(async file => ({ path: file, sha256: sha256(await readFile(path.join(repo, file))) })));
let sourceBaseline = 'unavailable';
try { sourceBaseline = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim(); } catch { /* A source export may have no .git directory. */ }
const VERSION = '0.4.0';
const info = { product: '背包 DP · 独立互动课', version: VERSION, status: 'standalone preview; not a TB release', builtAt: new Date().toISOString(), sourceBaseline, sourceIdentity: 'SHA-256 manifest of the working sources below', sources, files: { '开始体验.html': sha256(html) } };
const licenses = await Promise.all(['react', 'react-dom', 'lucide-react'].map(async name => `${name}\n${await readFile(path.join(frontend, 'node_modules', name, 'LICENSE'), 'utf8')}`));
const files = {
  '开始体验.html': html,
  '使用说明.txt': `背包 DP · 独立互动课 ${VERSION}\r\n\r\n解压整个压缩包后，双击“开始体验.html”，用 Edge 或 Chrome 打开。\r\n无需安装、联网或启动服务器。右上角“目录”可切换七节课程。“跟做”可进入五道精选题。\r\n输入、提示和练习进度保存在当前浏览器中；关闭再开可以继续。\r\n换浏览器、移动文件位置或清除浏览器数据后，原进度可能无法继续。\r\n“打开原题”需要联网；C++ 完整程序请在自己的编译器中运行。\r\n\r\n这是可单独使用的体验包；TB 主应用另提供进入工作台实现的入口。\r\n`,
  'README.en.txt': `Knapsack DP — standalone interactive course ${VERSION}\r\n\r\nExtract the ZIP and open 开始体验.html in Edge or Chrome.\r\nNo installation, network access or server is required for the course.\r\nThe menu switches between seven lessons. The guided-practice button opens five selected problems. Progress stays in this browser.\r\nChanging browser or file location, or clearing browser data, may reset access to saved progress.\r\nThe optional original-problem link requires internet access. Run full C++ programs in your own compiler.\r\nThis preview is separate from the TB desktop application.\r\n`,
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
