// ローカル開発サーバ。依存パッケージなし。
//
//     node server.mjs          → http://localhost:4321
//     PORT=5000 node server.mjs
//
// Vercel の Node ランタイムと同じハンドラ（api/*.js）をそのまま呼ぶので、
// ローカルで動いたものは Vercel でも同じように動く。
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(ROOT, 'public');
const PORT = Number(process.env.PORT) || 4321;

const ROUTES = {
  '/api/auth': () => import('./api/auth.js'),
  '/api/meta': () => import('./api/meta.js'),
  '/api/orders': () => import('./api/orders.js'),
  '/api/reports': () => import('./api/reports.js'),
};

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.csv': 'text/csv; charset=utf-8',
};

/** Vercel のハンドラが期待する res.status()/res.json() を生やす */
function decorate(res) {
  res.status = (code) => ((res.statusCode = code), res);
  res.json = (body) => {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.end(JSON.stringify(body));
    return res;
  };
  res.send = (body) => (res.end(body), res);
  return res;
}

async function serveStatic(req, res, pathname) {
  // 拡張子なしのパスは .html を補う（/orders → /orders.html）
  let rel = pathname === '/' ? '/index.html' : pathname;
  if (!path.extname(rel)) rel += '.html';
  const file = path.join(PUBLIC, path.normalize(rel).replace(/^(\.\.[/\\])+/, ''));
  if (!file.startsWith(PUBLIC)) {
    res.statusCode = 403;
    return res.end('Forbidden');
  }
  try {
    const body = await fs.readFile(file);
    res.statusCode = 200;
    res.setHeader('Content-Type', MIME[path.extname(file)] || 'application/octet-stream');
    res.setHeader('Cache-Control', 'no-store');
    res.end(body);
  } catch {
    res.statusCode = 404;
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end('<h1>404</h1><p><a href="/">トップへ</a></p>');
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  decorate(res);
  const route = ROUTES[url.pathname];
  if (route) {
    try {
      const mod = await route();
      req.query = Object.fromEntries(url.searchParams.entries());
      await mod.default(req, res);
    } catch (err) {
      console.error(err);
      if (!res.headersSent) res.statusCode = 500;
      res.end(JSON.stringify({ error: 'internal_error', message: String(err) }));
    }
    return;
  }
  await serveStatic(req, res, url.pathname);
});

const { USERS, DEFAULT_PASSWORD } = await import('./api/_data.js');

server.listen(PORT, () => {
  const shown = process.env.RPA_SALES_PASSWORD || process.env.RPA_APPROVER_PASSWORD
    ? '（環境変数で設定した値）'
    : DEFAULT_PASSWORD;
  console.log(`
  Altair 受注管理（RPA練習用）
  → http://localhost:${PORT}

  ログイン情報（練習用のダミーです）
    営業        ${USERS[0].email}
    承認者      ${USERS[1].email}
    パスワード  ${shown}

  RPA_SALES_PASSWORD / RPA_APPROVER_PASSWORD で変更できます。
`);
});
