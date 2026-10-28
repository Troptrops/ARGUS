"""Safe NPZ geometry adapter; adapted from ARGUS 8.2 NPY member reader.

No CT tensor is loaded. Stored coordinates remain registration-unverified.
"""
import array
import ast
import hashlib
import math
import struct
import sys
import zipfile


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def member(archive, name):
    info = archive.getinfo(name+'.npy')
    if info.file_size > 32_000_000:
        raise ValueError('Oversize geometry member')
    with archive.open(info) as stream:
        if stream.read(6) != b'\x93NUMPY':
            raise ValueError('Invalid NPY magic')
        version = stream.read(2)
        if version not in (b'\x01\x00', b'\x02\x00', b'\x03\x00'):
            raise ValueError('Unsupported NPY version')
        size = 2 if version[0] == 1 else 4
        length = int.from_bytes(stream.read(size), 'little')
        if length > 100_000:
            raise ValueError('Oversize NPY header')
        header = ast.literal_eval(stream.read(length).decode('utf8' if version[0] == 3 else 'latin1'))
        shape, dtype = header['shape'], header['descr']
        if header['fortran_order']:
            raise ValueError('Geometry maps must use C order')
        codes = {'<f4':'f', '<f8':'d', '<i4':'i', '<i8':'q', '|u1':'B', '|b1':'B'}
        if dtype not in codes or not isinstance(shape, tuple) or any(type(v) is not int or v < 0 for v in shape):
            raise ValueError('Unsupported geometry dtype/shape')
        values = array.array(codes[dtype])
        count = math.prod(shape)*values.itemsize
        if count > 32_000_000:
            raise ValueError('Oversize geometry payload')
        raw = stream.read(count+1)
        if len(raw) != count:
            raise ValueError('Incorrect NPY payload length')
        values.frombytes(raw)
        if sys.byteorder != 'little':
            values.byteswap()
        return shape, values


def load_map(path, mask_key='region12_mask', limit=0, controls=0, seed=1729):
    """All masked pixels, or fixed geometry-only stratified subset. No intensity selection.

    Supports surface_z+raw_x0/raw_y0 or native x/y/z maps; normals use nx,ny,nz.
    Controls are sampled outside the mask on the SAME map and are local diagnostics.
    """
    import random
    with zipfile.ZipFile(path) as archive:
        shape, mask = member(archive, mask_key)
        if len(shape) != 2 or not all(shape):
            raise ValueError('Expected nonempty 2-D mask')
        h,w = shape
        names = set(archive.namelist())
        zkey = 'surface_z' if 'surface_z.npy' in names else 'z'
        zshape, zz = member(archive,zkey)
        if zshape != shape:
            raise ValueError('Surface and mask shape mismatch')
        xy = {}
        for key in ('x','y'):
            if key+'.npy' in names:
                sh, vals = member(archive,key)
                if sh != shape:
                    raise ValueError('Coordinate map shape mismatch')
                xy[key] = vals
            else:
                sh, vals = member(archive,'raw_'+key+'0')
                if sh != () or len(vals) != 1 or not math.isfinite(vals[0]):
                    raise ValueError('Invalid native origin')
                xy[key+'0'] = vals[0]
        normals = {}
        for key in ('nx','ny','nz'):
            if key+'.npy' in names:
                sh, normals[key] = member(archive,key)
                if sh != shape:
                    raise ValueError('Normal and mask shape mismatch')
        indices = [i for i,v in enumerate(mask) if v]
        total = len(indices)
        if not total:
            raise ValueError('Empty ROI')
        if limit and len(indices) > limit:
            indices = [indices[min(total-1, (2*k+1)*total//(2*limit))] for k in range(limit)]
        selected = [(i,'roi') for i in indices]
        if controls:
            available = [i for i,v in enumerate(mask) if not v and math.isfinite(zz[i])]
            selected += [(i,'local_control') for i in random.Random(seed).sample(available,min(controls,len(available)))]
        points = []
        for i,group in selected:
            y,x = divmod(i,w)
            point = {'id':f'{group}_{y}_{x}', 'group':group, 'map_yx':[y,x],
                'zyx':[zz[i], xy['y'][i] if 'y' in xy else xy['y0']+y,
                       xy['x'][i] if 'x' in xy else xy['x0']+x],
                'registration':'GEO_REGISTRATION_UNVERIFIED'}
            if len(normals) == 3:
                point['normal_xyz'] = [normals[n][i] for n in ('nx','ny','nz')]
            points.append(point)
    return {'coordinate_system':'NATIVE_CT_ZYX', 'source_sha256':file_hash(path),
        'geometry':{'mask_key':mask_key, 'shape_yx':shape, 'mask_pixel_count':total,
                    'selected_roi_points':len(indices), 'seed':seed,
                    'selection':'all_mask_pixels' if len(indices)==total else 'fixed_stratified_row_major',
                    'exact_micro_residual':False}, 'points':points}
