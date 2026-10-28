"""Small Zarr-v2 reader derived from ARGUS 8.0 decoding and 8.2 grouped reads.

Missing storage is retained separately from observed fill values. Arrays must be
explicitly supplied at the native level with Z,Y,X axes; no implicit resampling.
"""
import hashlib
import itertools
import json
import math
import re
import struct
import zlib


def validate(meta):
    if meta.get('zarr_format') != 2:
        raise ValueError('Only Zarr v2 is supported')
    for name in ('shape', 'chunks'):
        if len(meta.get(name, [])) != 3 or any(type(v) is not int or v <= 0 for v in meta[name]):
            raise ValueError('Expected positive 3-D '+name)
    if meta.get('order') not in ('C', 'F'):
        raise ValueError('Unsupported memory order')
    if meta.get('dimension_separator', '.') not in ('.', '/'):
        raise ValueError('Unsupported separator')
    if meta.get('filters'):
        raise ValueError('Zarr filters require an explicit compatible decoder')
    dtype_format(meta['dtype'])
    return meta


def dtype_format(dtype):
    match = re.fullmatch(r'([<>|=])([uif])(1|2|4|8)', dtype)
    if not match:
        raise ValueError('Unsupported dtype')
    endian, kind, size = match.groups()
    codes = {'u': {'1':'B','2':'H','4':'I','8':'Q'},
             'i': {'1':'b','2':'h','4':'i','8':'q'}, 'f': {'2':'e','4':'f','8':'d'}}
    if size not in codes[kind] or (endian == '|' and size != '1'):
        raise ValueError('Invalid dtype size or byte order')
    return ('<' if endian == '|' else endian)+codes[kind][size], int(size)


def nearest(point, shape):
    if not isinstance(point, (list, tuple)) or len(point) != 3:
        raise ValueError('Expected native ZYX triple')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) or v < 0 or v > n-1 for v,n in zip(point,shape)):
        raise ValueError('Nonfinite or out-of-volume coordinate')
    return tuple(math.floor(v+0.5) for v in point)


class Volume:
    def __init__(self, base, transport, decode_blosc=False):
        self.base, self.transport = str(base).rstrip('/'), transport
        self.decode_blosc = decode_blosc
        status, raw = transport.get(self.base+'/.zarray')
        if status != 200:
            raise ValueError('Zarr array metadata unavailable')
        self.meta = validate(json.loads(raw))
        self.metadata_sha256 = hashlib.sha256(raw).hexdigest()
        self.cache = {}

    def key(self, point):
        return self.meta.get('dimension_separator', '.').join(
            str(v//c) for v,c in zip(point, self.meta['chunks']))

    def chunk(self, key, presence=False):
        cache_key = key, presence
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            status, raw = self.transport.get(self.base+'/'+key, 'HEAD' if presence else 'GET')
            if status == 404:
                result = ('CHUNK_ABSENT_404', None)
            elif presence:
                result = ('CHUNK_PRESENT_ONLY', None)
            else:
                codec = self.meta.get('compressor')
                expected = math.prod(self.meta['chunks'])*dtype_format(self.meta['dtype'])[1]
                if expected > self.transport.max_response:
                    raise ValueError('Decoded chunk exceeds configured response limit')
                if codec:
                    cid = codec.get('id')
                    if cid in ('gzip', 'zlib'):
                        decoder = zlib.decompressobj(31 if cid == 'gzip' else 15)
                        raw = decoder.decompress(raw, expected+1)
                        if not decoder.eof or decoder.unused_data:
                            raise ValueError('Truncated or oversized compressed chunk')
                    elif cid == 'blosc' and self.decode_blosc:
                        import numcodecs
                        if len(raw) < 16 or struct.unpack_from('<I',raw,4)[0] != expected:
                            raise ValueError('Blosc declared size differs from chunk shape')
                        raw = bytes(numcodecs.get_codec(codec).decode(raw))
                    else:
                        raise ValueError('Unsupported codec; install optional decoder and enable explicitly')
                if len(raw) != expected:
                    raise ValueError('Decoded chunk byte length differs from full chunk shape')
                result = ('DECODED', raw)
        except Exception as exc:
            result = ('INDETERMINATE', type(exc).__name__+': '+str(exc))
        self.cache[cache_key] = result
        return result

    def voxel(self, point):
        if any(v < 0 or v >= n for v,n in zip(point,self.meta['shape'])):
            return {'state':'OUT_OF_BOUNDS', 'value':None}
        key = self.key(point)
        state, raw = self.chunk(key)
        result = {'state':state, 'value':None, 'chunk_key':key}
        if state == 'INDETERMINATE':
            result['error'] = raw
        if state != 'DECODED':
            return result
        z,y,x = (v%c for v,c in zip(point,self.meta['chunks']))
        a,b,c = self.meta['chunks']
        index = (z*b+y)*c+x if self.meta['order'] == 'C' else z+a*(y+b*x)
        fmt, size = dtype_format(self.meta['dtype'])
        value = struct.unpack_from(fmt, raw, index*size)[0]
        if not math.isfinite(value):
            return {**result, 'state':'INDETERMINATE', 'error':'Nonfinite CT scalar'}
        return {**result, 'state':'CT_VOXEL_NONZERO' if value != 0 else 'CT_VOXEL_ZERO', 'value':value}

    def observe(self, point, radius=2, mode='surface-support'):
        try:
            center = nearest(point, self.meta['shape'])
        except ValueError as exc:
            return {'state':'INVALID_COORDINATE', 'error':str(exc)}
        if mode == 'chunk-only':
            state, error = self.chunk(self.key(center), presence=True)
            return {'state':state, 'sampled_zyx':center,
                    'error':error, 'evidence_level':'CHUNK_KEY_EXISTENCE_ONLY'}
        result = {**self.voxel(center), 'sampled_zyx':center,
                  'rounding_error_zyx':[v-u for v,u in zip(center,point)]}
        if mode == 'voxel':
            return result
        observations = [self.voxel(q) for q in itertools.product(
            *(range(v-radius,v+radius+1) for v in center))]
        valid = [r['value'] for r in observations if r['value'] is not None]
        complete = len(valid) == len(observations)
        from collections import Counter
        result['neighborhood'] = {'expected_n':len(observations), 'observed_n':len(valid),
            'complete':complete, 'state_counts':dict(Counter(r['state'] for r in observations)),
            'observed_nonzero_fraction':sum(v != 0 for v in valid)/len(valid) if valid else None,
            'nonzero_fraction':sum(v != 0 for v in valid)/len(valid) if complete else None}
        return result
