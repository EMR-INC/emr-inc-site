"""Carry one verified server function into a clean, locally prebuilt public edition."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib import parse, request

TEAM = 'team_rwxqo0kDlEjDlDdXAJv9y7e6'
PROJECT = 'prj_kiJjgBMbwd070fbCefZ3zz1Uv9E4'
FUNCTION = 'functions/api/ohpah-gateway.func'
PREFIX = 'src/.vercel/output/' + FUNCTION + '/'
LOCK = Path(__file__).with_name('release-lock.json')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api(path):
    url = 'https://api.vercel.com' + path + '?teamId=' + TEAM
    req = request.Request(url, headers={'Authorization':'Bearer ' + os.environ['VERCEL_TOKEN']})
    with request.build_opener(NoRedirect()).open(req, timeout=15) as response:
        raw = response.read(4_000_001)
        if len(raw)>4_000_000:
            raise ValueError('Unexpected API response size')
        return json.loads(raw)


def members(items, prefix=''):
    for item in items:
        name = item['name']
        if not name or '/' in name or name in ('.','..') or '\\' in name:
            raise ValueError('Invalid provider path')
        path = prefix + name
        if item['type']=='directory':
            yield from members(item.get('children',[]),path+'/')
        elif path.startswith(PREFIX):
            if item['type']!='file' or not re.fullmatch('[a-f0-9]{40}',item['uid']):
                raise ValueError('Unexpected function member')
            yield path[len(PREFIX):],item['uid']


def validate_static(output):
    for folder in ('static','functions'):
        for p in (output/folder).rglob('*'):
            if p.is_symlink():
                raise ValueError('Unreviewed build link')
            name=parse.unquote(p.relative_to(output/folder).as_posix()).casefold()
            if name=='ohpah' or name.startswith(('ohpah.','ohpah/','api/ohpah','api/_lib/ohpah')):
                raise ValueError('Public output shadows a private route')


def restore(output, source, get=api):
    if source!='emr-inc.net' and not re.fullmatch('dpl_[A-Za-z0-9]+', source):
        raise ValueError('Invalid deployment identifier')
    lock=json.loads(LOCK.read_bytes())
    metadata=get('/v13/deployments/'+source)
    identifier=metadata['id']
    if (not re.fullmatch('dpl_[A-Za-z0-9]+',identifier) or metadata.get('projectId')!=PROJECT
            or metadata.get('ownerId')!=TEAM or metadata.get('public') is not False
            or metadata.get('readyState')!='READY' or metadata.get('target')!='production'
            or (source!='emr-inc.net' and identifier!=source)):
        raise ValueError('Source must be a private-source ready production deployment in this project')
    rows=list(members(get('/v6/deployments/'+identifier+'/files')))
    files=dict(rows)
    if len(files)!=len(rows) or files.keys()!=lock['members'].keys():
        raise ValueError('Deployment lacks the approved workload function inventory')
    validate_static(output)
    config=json.loads((output/'config.json').read_bytes())
    canonical=json.dumps(config['routes'],sort_keys=True,separators=(',',':')).encode()
    if digest(canonical)!=lock['public_routes_sha256']:
        raise ValueError('Public routing changed and needs review')
    i=config['routes'].index(lock['insert_before'])
    config['routes'][i:i]=lock['integrated_routes']
    # The staging directory stays outside static and is destroyed on any failed read.
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        tmp=Path(tmp)
        tree=tmp/'function'
        for name,(size,expected) in lock['members'].items():
            res=get('/v8/deployments/'+identifier+'/files/'+files[name])
            raw=base64.b64decode(res['data'],validate=True)
            if len(raw)!=size or digest(raw)!=expected:
                raise ValueError('Function content differs from release lock')
            dst=tree/name
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(raw)
        dest=output/FUNCTION
        if dest.exists() or dest.is_symlink():
            raise ValueError('Existing gateway needs review')
        next_config=tmp/'config.json'
        next_config.write_text(json.dumps(config)+'\n')
        tree.rename(dest)
        try:
            next_config.replace(output/'config.json')
        except BaseException:
            shutil.rmtree(dest)
            raise
    return {'source_deployment':identifier,'verified_files':len(files),'verified_bytes':sum(x[0] for x in lock['members'].values())}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--source',default='emr-inc.net')
    args=parser.parse_args()
    print(json.dumps(restore(args.output,args.source)))
