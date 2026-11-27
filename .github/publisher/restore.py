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
    locks=[json.loads(p.read_bytes()) for p in (LOCK,LOCK.with_name('reviewed-release-lock.json'))]
    metadata=get('/v13/deployments/'+source)
    identifier=metadata['id']
    if (not re.fullmatch('dpl_[A-Za-z0-9]+',identifier) or metadata.get('projectId')!=PROJECT
            or metadata.get('ownerId')!=TEAM or metadata.get('public') is not False
            or metadata.get('readyState')!='READY' or metadata.get('target')!='production'
            or (source!='emr-inc.net' and identifier!=source)):
        raise ValueError('Source must be a private-source ready production deployment in this project')
    rows=list(members(get('/v6/deployments/'+identifier+'/files')))
    files=dict(rows)
    candidates=[lock for lock in locks if files.keys()==lock['members'].keys()]
    if len(files)!=len(rows) or len(candidates)!=1:
        raise ValueError('Deployment lacks the approved workload function inventory')
    lock=candidates[0]
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
        verified_bytes=0
        for name,(size,expected) in lock['members'].items():
            res=get('/v8/deployments/'+identifier+'/files/'+files[name])
            raw=base64.b64decode(res['data'],validate=True)
            observed=[len(raw),digest(raw)]
            accepted=[[size,expected]]
            variant=lock.get('form_gateway_variant',{})
            if name=='api/_lib/ohpah/gateway.mjs' and variant.get('baseline')==accepted[0]:
                accepted.append(variant['approved'])
            if observed not in accepted:
                raise ValueError('Function content differs from release lock')
            verified_bytes+=len(raw)
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
    return {'source_deployment':identifier,'verified_files':len(files),'verified_bytes':verified_bytes}


REVIEWED_SEED = 'dpl_5a6cc8pNacMNsUegFULtrdsVCc28'

def first_reviewed_release(output, get=api):
    serving=get('/v13/deployments/emr-inc.net')
    rollback=serving.get('id','')
    if (not re.fullmatch('dpl_[A-Za-z0-9]+',rollback) or serving.get('ownerId')!=TEAM
            or serving.get('projectId')!=PROJECT or serving.get('target')!='production'
            or serving.get('readyState')!='READY' or serving.get('public') is not False):
        raise ValueError('Unexpected rollback deployment')
    previous=list(members(get('/v6/deployments/'+rollback+'/files')))
    original=json.loads(LOCK.read_bytes())['members']
    if len(previous)!=len(original) or dict(previous).keys()!=original.keys():
        raise ValueError('First activation is only valid from the original workload release')
    result=restore(output, REVIEWED_SEED, get)
    if result['verified_files']!=len(json.loads(LOCK.with_name('reviewed-release-lock.json').read_bytes())['members']):
        raise ValueError('Reviewed release did not match')
    result['rollback_deployment']=rollback
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--source',default='emr-inc.net')
    parser.add_argument('--activate-reviewed',action='store_true')
    args=parser.parse_args()
    if args.activate_reviewed and args.source!='emr-inc.net':parser.error('Activation uses the pinned seed only')
    print(json.dumps(first_reviewed_release(args.output) if args.activate_reviewed else restore(args.output,args.source)))
