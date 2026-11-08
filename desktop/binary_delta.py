"""Bounded BSDIFF40 blocks; source and complete output are SHA-256 bound.

Only the release builder uses bsdiff4. Desktop decoding uses the standard
library and never loads executable code from an update payload.
"""
import bz2
import hashlib
import json
from pathlib import Path
import re
import struct

MAGIC=b'TBBD1\r\n\x00'
MAX_BLOCK=8*1024*1024
MAX_FILE=2*1024**3
NONZERO=re.compile(b'[^\x00]+')


def signed(data):
    value=int.from_bytes(data,'little')
    return -(value&0x7fffffffffffffff) if value>>63 else value


def inflate(data,maximum):
    decoder=bz2.BZ2Decompressor()
    value=decoder.decompress(data,max_length=maximum+1)
    if len(value)>maximum or not decoder.eof or decoder.unused_data:
        raise ValueError('差分压缩块超出范围或不完整')
    return value


def patch_block(source,patch):
    if len(source)>MAX_BLOCK or len(patch)>MAX_BLOCK*2 or len(patch)<32 or patch[:8]!=b'BSDIFF40':
        raise ValueError('差分块格式无效')
    control_size,diff_size,size=(signed(patch[i:i+8]) for i in (8,16,24))
    if min(control_size,diff_size,size)<0 or size>MAX_BLOCK or 32+control_size+diff_size>len(patch):
        raise ValueError('差分块长度无效')
    boundary=32+control_size
    control=inflate(patch[32:boundary],min(MAX_BLOCK,(size+1)*24))
    differences=inflate(patch[boundary:boundary+diff_size],size)
    extras=inflate(patch[boundary+diff_size:],size)
    if len(control)%24:raise ValueError('差分操作不完整')
    output=bytearray(size);old=position=diff_at=extra_at=0
    for at in range(0,len(control),24):
        count,extra,seek=(signed(control[i:i+8]) for i in (at,at+8,at+16))
        if count<0 or extra<0 or position+count+extra>size or diff_at+count>len(differences) or extra_at+extra>len(extras):
            raise ValueError('差分操作越界')
        # BSDIFF permits an old cursor outside the source; those bytes are zero.
        low=max(0,old);high=min(len(source),old+count)
        if high>low:output[position+low-old:position+high-old]=source[low:high]
        delta=differences[diff_at:diff_at+count]
        for match in NONZERO.finditer(delta):
            start,end=match.span();offset=position+start
            output[offset:position+end]=bytes((a+b)&255 for a,b in zip(output[offset:position+end],delta[start:end]))
        position+=count;old+=count;diff_at+=count
        output[position:position+extra]=extras[extra_at:extra_at+extra]
        position+=extra;extra_at+=extra;old+=seek
    if position!=size or diff_at!=len(differences) or extra_at!=len(extras):
        raise ValueError('差分操作与输出长度不一致')
    return bytes(output)


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def file_delta(source,payload,destination,*,expected_target):
    source,payload,destination=map(Path,(source,payload,destination))
    if not re.fullmatch('[a-f0-9]{64}',expected_target):raise ValueError('目标摘要无效')
    if source.is_symlink() or payload.is_symlink() or destination.exists():raise ValueError('差分文件路径无效或目标已存在')
    with payload.open('rb') as stream:
        if stream.read(8)!=MAGIC:raise ValueError('文件差分格式无效')
        raw_length=stream.read(4)
        if len(raw_length)!=4:raise ValueError('文件差分清单缺失')
        length=struct.unpack('<I',raw_length)[0]
        if not 0<length<=4*1024**2:raise ValueError('文件差分清单过大')
        raw=stream.read(length)
        if len(raw)!=length:raise ValueError('文件差分清单不完整')
        info=json.loads(raw)
        if not isinstance(info,dict) or info.get('schema')!=1 or info.get('targetSha256')!=expected_target:raise ValueError('文件差分目标不匹配')
        if type(info.get('sourceBytes')) is not int or not 0<=info['sourceBytes']<=MAX_FILE or type(info.get('targetBytes')) is not int or not 0<=info['targetBytes']<=MAX_FILE:
            raise ValueError('文件差分范围无效')
        if source.stat().st_size!=info['sourceBytes'] or digest(source)!=info.get('sourceSha256'):
            raise ValueError('文件差分基线不匹配')
        blocks=info.get('blocks')
        if not isinstance(blocks,list) or len(blocks)>4096:raise ValueError('文件差分块数无效')
        for block in blocks:
            if not isinstance(block,dict):raise ValueError('文件差分块无效')
            if any(type(block.get(key)) is not int for key in ('sourceOffset','sourceBytes','targetBytes','patchBytes')):
                raise ValueError('文件差分块范围无效')
            if not 0<=block['sourceOffset']<=info['sourceBytes'] or not 0<=block['sourceBytes']<=MAX_BLOCK or block['sourceOffset']+block['sourceBytes']>info['sourceBytes'] or not 0<=block['targetBytes']<=MAX_BLOCK or not 32<=block['patchBytes']<=MAX_BLOCK*2:
                raise ValueError('文件差分块越界')
            if not isinstance(block.get('patchSha256'),str) or not re.fullmatch('[a-f0-9]{64}',block['patchSha256']):raise ValueError('文件差分块摘要无效')
        if sum(block['targetBytes'] for block in blocks)!=info['targetBytes']:raise ValueError('文件差分总长度不一致')
        output_hash=hashlib.sha256();total=0
        with source.open('rb') as original,destination.open('xb') as output:
            for block in blocks:
                patch=stream.read(block['patchBytes'])
                if len(patch)!=block['patchBytes'] or hashlib.sha256(patch).hexdigest()!=block['patchSha256']:
                    raise ValueError('文件差分块校验失败')
                original.seek(block['sourceOffset']);old=original.read(block['sourceBytes'])
                if len(old)!=block['sourceBytes']:raise ValueError('差分基线读取不完整')
                value=patch_block(old,patch)
                if len(value)!=block['targetBytes']:raise ValueError('差分输出块长度不一致')
                output.write(value);output_hash.update(value);total+=len(value)
        if stream.read(1) or total!=info['targetBytes'] or output_hash.hexdigest()!=expected_target:
            raise ValueError('完整差分输出未通过校验')
    return {'bytes':total,'sha256':expected_target}
