// Serveur local de recette : sert le site ET exécute le vrai Worker (src/index.js), comme Cloudflare.
// Usage : node tests/serveur-local.mjs [port]   — les demandes reçues s'affichent dans la console.
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { join, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import worker from '../src/index.js';

const PUB = join(dirname(fileURLToPath(import.meta.url)), '..', 'public');
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.xml': 'application/xml', '.txt': 'text/plain' };
const ASSETS = { async fetch(req) {
  let p = new URL(req.url).pathname; if (p.endsWith('/')) p += 'index.html';
  try { return new Response(await readFile(join(PUB, p)), { headers: { 'Content-Type': TYPES[extname(p)] || 'application/octet-stream' } }); }
  catch { return new Response(await readFile(join(PUB, '404.html')), { status: 404, headers: { 'Content-Type': TYPES['.html'] } }); }
} };
const memo = new Map();
globalThis.caches = { default: { async match(r) { return memo.get(r.url); }, async put(r, v) { memo.set(r.url, v); } } };
const env = { ASSETS, ENVIRONNEMENT: 'preproduction', PROTECTION: 'aucune' };

http.createServer(async (rq, rs) => {
  const chunks = []; for await (const c of rq) chunks.push(c);
  const corps = chunks.length ? Buffer.concat(chunks) : undefined;
  const r = await worker.fetch(new Request('http://localhost' + rq.url, { method: rq.method, headers: rq.headers, body: corps }), env);
  const h = {}; r.headers.forEach((v, k) => { h[k] = v; });
  rs.writeHead(r.status, h); rs.end(Buffer.from(await r.arrayBuffer()));
}).listen(+process.argv[2] || 8787, () => console.log('recette locale prête'));
