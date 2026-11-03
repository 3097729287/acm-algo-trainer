import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';

export const RELEASE_STREAM_PROXY=`    # Existing assets remain local. An approved new asset can be streamed from
    # the published release without filling the account server's filesystem.
    @missing_asset {
      path /assets/*
      not file {path}
    }
    reverse_proxy @missing_asset api:8080
`;
export function releaseStreamProxy(current){
 if(typeof current!=='string')throw new Error('Expected the current Caddyfile');
 const marker='    header @assets Cache-Control "public, max-age=31536000, immutable"\n';
 if(current.split(marker).length!==2)throw new Error('The public asset route is not unique');
 if(current.includes(RELEASE_STREAM_PROXY))return current;
 if(current.includes('@missing_asset'))throw new Error('An unreviewed asset route already exists');
 return current.replace(marker,marker+RELEASE_STREAM_PROXY);
}
if(process.argv[1]&&fileURLToPath(import.meta.url).toLowerCase()===resolve(process.argv[1]).toLowerCase()){
 if(process.argv.length!==4)throw new Error('Provide current and candidate Caddyfile paths');
 await writeFile(process.argv[3],releaseStreamProxy(await readFile(process.argv[2],'utf8')),'utf8');
}
