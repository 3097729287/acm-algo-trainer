"""Compact immutable catalogue snapshots; callers still own decoded records."""
import base64
import gzip

PLAIN_LIMIT = 64 * 1024


def pack(raw):
    return gzip.compress(raw, compresslevel=1, mtime=0) if len(raw) > PLAIN_LIMIT else raw


def unpack(value):
    return gzip.decompress(value) if value.startswith(b'\x1f\x8b') else value


def response(value, compressed=False):
    if compressed and value.startswith(b'\x1f\x8b'):
        from response_cache import GzipJSON
        return GzipJSON(value)
    return unpack(value)


def document(value):
    if value.startswith(b'\x1f\x8b'):
        return {'catalogGzip': base64.b64encode(value).decode('ascii')}
    return {'catalog': value.decode('utf-8')}


def from_document(value):
    if isinstance(value.get('catalogGzip'), str):
        return base64.b64decode(value['catalogGzip'], validate=True)
    return value['catalog'].encode('utf-8')
