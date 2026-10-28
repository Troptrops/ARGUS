"""Hash Git-tracked release files; stage intended files before running."""
import hashlib
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    names=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode('utf8').split('\0')
    rows=[]
    for name in sorted(set(names)):
        if not name or name=='FILE_SHA256.txt':continue
        path=root/name
        if not path.is_file():raise ValueError('Stage deletions first: '+name)
        rows.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+name)
    (root/'FILE_SHA256.txt').write_text('\n'.join(rows)+'\n',encoding='utf8')
    print('Manifest entries:',len(rows))


if __name__=='__main__':main()
