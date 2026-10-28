"""Offline release manifest, link and package checks; no external data required."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote


def check(root):
    root=Path(root).resolve()
    version=re.search(r'^version = "([^"]+)"',(root/'pyproject.toml').read_text(),re.M).group(1)
    namespace={}
    exec((root/'argus_support/__init__.py').read_text(encoding='utf8'),namespace)
    if version!=namespace['__version__']:raise ValueError('Packaging/runtime versions disagree')
    checked=0
    for line in (root/'FILE_SHA256.txt').read_text().splitlines():
        digest,name=line.split('  ',1)
        f=(root/name).resolve()
        if not f.is_relative_to(root) or not f.is_file():raise ValueError('Missing or unsafe manifest path: '+name)
        if hashlib.sha256(f.read_bytes()).hexdigest()!=digest:raise ValueError('SHA256 mismatch: '+name)
        checked+=1
    broken=[]
    for folder in [root,root/'docs']:
        for f in folder.glob('*.md'):
            if f.name=='ORIGINAL_TECHNICAL_README.md':continue
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding='utf-8-sig')):
                target=target.split('#',1)[0]
                if not target or '://' in target or target.startswith('mailto:'):continue
                if not (f.parent/unquote(target)).exists():broken.append((str(f.relative_to(root)),target))
    if broken:raise ValueError('Broken local links: '+json.dumps(broken))
    for name in ['argus_support','tools','tests','protocol','evidence','figures','research','docs']:
        if not (root/name).is_dir():raise ValueError('Missing release folder '+name)
    print('Release checks: PASS; version',version,';',checked,'manifest entries; main/docs links resolve')


if __name__=='__main__':check(Path(__file__).resolve().parents[1])
