// POST /api/auth        { email, password }  → ログイン
// GET  /api/auth        → 現在のセッション
// DELETE /api/auth      → ログアウト
import { USERS } from './_data.js';
import {
  issueToken, verifyToken, readCookies, setSessionCookie, clearSessionCookie,
  COOKIE_NAME, SESSION_TTL_MS, checkLock, recordFailure, recordSuccess,
} from './_auth.js';
import { json, latency, readBody } from './_http.js';

export default async function handler(req, res) {
  if (req.method === 'GET') {
    const s = verifyToken(readCookies(req)[COOKIE_NAME]);
    if (!s) return json(res, 401, { error: 'unauthenticated' });
    const { password, ...user } = s.user;
    return json(res, 200, { user, expiresAt: s.expiresAt, ttlMs: SESSION_TTL_MS });
  }

  if (req.method === 'DELETE') {
    clearSessionCookie(res);
    return json(res, 200, { ok: true });
  }

  if (req.method !== 'POST') return json(res, 405, { error: 'method_not_allowed' });

  await latency(400, 900); // ログインは重い、という前提にしてある
  const { email, password } = await readBody(req);
  const addr = String(email || '').toLowerCase();

  const locked = checkLock(addr);
  if (locked) {
    return json(res, 429, {
      error: 'locked',
      message: `試行回数が上限に達しました。${locked}秒後に再試行してください。`,
      retryAfterSec: locked,
    });
  }

  const user = USERS.find((u) => u.email.toLowerCase() === addr);
  if (!user || user.password !== password) {
    recordFailure(addr);
    return json(res, 401, {
      error: 'invalid_credentials',
      message: 'メールアドレスまたはパスワードが違います。',
    });
  }

  recordSuccess(addr);
  setSessionCookie(res, issueToken(user));
  const { password: _p, ...safe } = user;
  return json(res, 200, { user: safe, ttlMs: SESSION_TTL_MS });
}
