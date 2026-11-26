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
           '.github/publisher/check.mjs','.github/publisher/verify_public.py','.github/publisher/reviewed-release-lock.json','.github/publisher/release-lock.json'}

PUBLISHER.add('.github/publisher/test_static.py')
# Only the site itself belongs in the static output. Verification still checks each
# included file against the reviewed Git revision, before restoring private functions.
SITE_FILES = PAGES | {
    'dispatch-views.js', 'reveal.js', 'member-research.html', 'open-data/index.html',
    'research/index.html', 'internal/research.html',
    'data/nfirs-hour-of-day.json', 'data/nfirs-incident-composition.json',
}
MEDIA_SUFFIXES = {
    'assets': {'.jpg', '.jpeg', '.png', '.svg', '.pdf', '.webp', '.json', '.css', '.js',
               '.mp4', '.avif', '.ico', '.gif'},
    'play': {'.png', '.txt', '.js', '.css', '.mp3', '.jpeg', '.html'},
}

def site_file(path):
    if any(part.startswith('.') for part in path.parts):
        return False
    return (path.as_posix() in SITE_FILES or
            len(path.parts) > 1 and path.suffix.lower() in MEDIA_SUFFIXES.get(path.parts[0], set()))

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
    root = Path.cwd().resolve()
    if output.resolve() != root / '.vercel/output/static' or any(
            (root / part).is_symlink() for part in ('.vercel', '.vercel/output', '.vercel/output/static')):
        raise ValueError('Unexpected static build directory')
    tree={}
    for row in git('ls-tree','-r','-z','HEAD').split(b'\0'):
        if row:
            meta,name=row.split(b'\t',1)
            tree[name.decode()]=meta.split()[-1]
    paths = list(output.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('Linked output')
    included = set()
    discarded = []
    for p in paths:
        if p.is_file():
            if not site_file(p.relative_to(output)):
                discarded.append(p)
                continue
            included.add(p.relative_to(output).as_posix())
            b=p.read_bytes()
            blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest().encode()
            if tree.get(p.relative_to(output).as_posix())!=blob:
                raise ValueError('Public output outside reviewed Git content')
    expected = {name for name in tree if site_file(Path(name))}
    if included != expected or not {'index.html', 'open-data.html', 'data/dispatch-views.json', 'research.html'} <= included:
        raise ValueError('Public edition incomplete')
    for p in discarded:
        p.unlink()
    for p in sorted((p for p in paths if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if not any(p.iterdir()):
            p.rmdir()

if __name__=='__main__':
    verify()
    if len(sys.argv)>1:
        static(Path(sys.argv[1]))
