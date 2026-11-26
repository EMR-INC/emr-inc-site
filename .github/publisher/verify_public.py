"""Ensure the already reviewed build inputs and public artifacts match the current commit."""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

BASE='32c5d713011b4ab0178961dbde481d80a85a1ebd'
PAGES={'index.html','contact.html','lab.html','play.html','dispatch-views.html','styles.css',
       'data/dispatch-views.json','data/research.json','open-data.html','research.html'}
PUBLISHER={'.github/workflows/dispatch-views.yml','.github/workflows/open_data_daily.yml',
           '.github/workflows/publish-integrated.yml','.github/publisher/restore.py',
           '.github/publisher/check.mjs','.github/publisher/verify_public.py','.github/publisher/release-lock.json'}

def git(*args):
    return subprocess.check_output(['git',*args])

def verify():
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    changed=git('diff','--no-renames','--name-only','-z',BASE,'HEAD').split(b'\0')
    for raw in filter(None,changed):
        name=raw.decode()
        if name not in PUBLISHER|PAGES and not re.fullmatch(
                r'assets/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-][A-Za-z0-9_.-]*\.(?:png|jpe?g|webp|gif|avif|ico|css)',name):
            raise ValueError('A changed public build input needs release review')
        row=git('ls-tree','HEAD','--',name)
        if row and not row.startswith(b'100644 blob '):
            raise ValueError('Unexpected tracked file type')

def static(output):
    tree={}
    for row in git('ls-tree','-r','-z','HEAD').split(b'\0'):
        if row:
            meta,name=row.split(b'\t',1)
            tree[name.decode()]=meta.split()[-1]
    for p in output.rglob('*'):
        if p.is_symlink():raise ValueError('Linked output')
        if p.is_file():
            b=p.read_bytes()
            blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest().encode()
            if tree.get(p.relative_to(output).as_posix())!=blob:
                raise ValueError('Public output outside reviewed Git content')
    if not all((output/n).is_file() for n in ('index.html','open-data.html','data/dispatch-views.json','research.html')):
        raise ValueError('Public edition incomplete')

if __name__=='__main__':
    verify()
    if len(sys.argv)>1:
        static(Path(sys.argv[1]))
