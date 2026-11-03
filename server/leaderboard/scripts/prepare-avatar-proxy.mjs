import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
export const ORIGINAL_AVATAR_PROXY=`  # Bounded, authenticated original portrait uploads; other limits stay fixed.
  @original_avatar {
    method PUT
    path /v1/profile
  }
  handle @original_avatar {
    request_body {
      max_size 16065568
    }
    reverse_proxy api:8080
  }
`;
export function originalAvatarProxy(source){
 if(source.includes('@original_avatar')){
  if(!source.includes(ORIGINAL_AVATAR_PROXY)||source.split('@original_avatar').length!==3)throw new Error('Unexpected original-avatar proxy configuration');
  return source;
 }
 const anchor='  handle {\n    request_body {\n      max_size 65536\n';
 if(source.split(anchor).length!==2)throw new Error('The existing bounded default proxy was not found exactly once');
 return source.replace(anchor,ORIGINAL_AVATAR_PROXY+anchor);
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const [input,output]=process.argv.slice(2);if(!input||!output)throw new Error('Provide the existing Caddyfile and a new candidate file');
 await writeFile(output,originalAvatarProxy(await readFile(input,'utf8')),{flag:'wx',mode:0o600});
}
