"""Thin optional adapter using villa's reader; no parallel mesh implementation.

Contract reviewed at villa 6aec908a85ed2ea674297ad4255fe1626c07a5c4,
vesuvius/src/vesuvius/tifxyz/API.md. Real tifxyz integration not yet exercised.
"""
import hashlib
from pathlib import Path
from .geometry import file_hash


def load_tifxyz(path, limit=0, reader=None):
    import numpy as np
    if reader is None:
        from vesuvius.tifxyz import read_tifxyz
        reader = read_tifxyz
    root = Path(path)
    hashes = {name:file_hash(root/name) for name in ('x.tif','y.tif','z.tif','meta.json')}
    if (root/'mask.tif').exists():
        hashes['mask.tif'] = file_hash(root/'mask.tif')
    surface = reader(str(path))
    surface.use_stored_resolution()
    x,y,z,valid = surface[:,:]
    if any(a.shape != x.shape for a in (y,z,valid)) or x.ndim != 2:
        raise ValueError('Incompatible tifxyz raster shapes')
    # Strict validity in addition to upstream mask: reject partial sentinels/nonfinite.
    keep = valid & np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (x>=0) & (y>=0) & (z>=0)
    indices = np.flatnonzero(keep)
    total = len(indices)
    if not total:
        raise ValueError('No valid tifxyz native coordinates')
    if limit and total > limit:
        indices = indices[((2*np.arange(limit)+1)*total//(2*limit)).clip(max=total-1)]
    if len(indices) > 100_000:
        raise ValueError('More than 100000 tifxyz vertices; set --limit')
    normals = surface.compute_normals()
    if len(normals) != 3 or any(n.shape != x.shape for n in normals):
        raise ValueError('Upstream normal raster shape mismatch')
    points = []
    for index in indices:
        row,col = divmod(int(index),x.shape[1])
        points.append({'id':f'vertex_{row}_{col}', 'group':'tifxyz_vertex', 'map_yx':[row,col],
            'zyx':[float(a[row,col]) for a in (z,y,x)],
            'normal_xyz':[float(a[row,col]) for a in normals],
            'normal_source':'upstream villa compute_normals at stored resolution',
            'registration':'GEO_REGISTRATION_UNVERIFIED'})
    import json
    return {'coordinate_system':'NATIVE_CT_ZYX', 'source_sha256':hashlib.sha256(
        json.dumps(hashes,sort_keys=True).encode()).hexdigest(),
        'geometry':{'format':'tifxyz', 'resolution':'stored', 'file_hashes':hashes,
                    'valid_vertices':total,'selected_vertices':len(points)}, 'points':points}
