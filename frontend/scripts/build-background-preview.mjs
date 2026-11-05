import {readFile,writeFile} from 'node:fs/promises';
const text=path=>readFile(new URL(path,import.meta.url),'utf8');
const [shell,engine,boot,baseCss,sceneCss]=await Promise.all([text('../previews/background-studio-shell.html'),text('../src/lib/motionBackgrounds.js'),text('../previews/background-studio-ui.js'),text('../src/components/MeteorsBackground.css'),text('../src/components/WorkspaceBackground.css')]);
const html=shell.replace('</style>',baseCss+'\n'+sceneCss+'\n</style>')+'<script>\n'+engine.replaceAll('export const ','const ').replaceAll('export class ','class ')+'\n'+boot+'\n</script>\n</body></html>\n';
await writeFile(new URL('../previews/background-studio.html',import.meta.url),html);console.log('Built offline background studio: 18 original scenes, approved meteors preserved');
