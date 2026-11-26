import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';

const root = resolve(process.argv[2]);
const cfg = JSON.parse(await readFile(root+'/config.json'));
const {default: gateway} = await import(pathToFileURL(root+'/functions/api/ohpah-gateway.func/api/ohpah-gateway.mjs'));
const server = createServer((req,res)=>{
  const rule=cfg.routes.find(r=>r.src && new RegExp(r.src).test(req.url) && r.dest?.includes('ohpah-gateway?'));
  if (!rule) {res.writeHead(404);res.end();return;}
  req.url=rule.dest;
  gateway(req,res);
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
try {
  const origin='http://127.0.0.1:'+server.address().port;
  const reviewed=cfg.routes.some(r=>r.src==='^/ohpah/calls$' && r.dest?.includes('ohpah-gateway?'));
  for (const [path,status] of [['/ohpah',303],['/ohpah/api/workload',401],['/ohpah/download',401],['/ohpah/calls',reviewed?303:404],['/ohpah/working-fires',reviewed?303:404],['/ohpah/api/calls',reviewed?401:404],['/ohpah/map',reviewed?303:404],['/ohpah/cei',reviewed?303:404]]) {
    const r=await fetch(origin+path,{redirect:'manual'});
    assert.equal(r.status,status,path);
    if (status!==404) assert.match(r.headers.get('cache-control'),/no-store/);
  }
} finally {server.close();}
