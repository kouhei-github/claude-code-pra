// セッション管理。HMAC-SHA256 で署名した httpOnly クッキーを使う。
//
// これは RPA の練習台であって、本番で使うことを想定した実装ではない。
// 学習者に「ログインを通らないとデータが1件も見えない」状態を作るのが目的。
import crypto from 'node:crypto';

import { USERS } from './_data.js';

const COOKIE = 'rpa_lab_session';
const TTL_MS = 30 * 60 * 1000; // 30分。RPAが「セッション切れ」を扱う練習のため短くしてある
// 署名鍵。未設定なら起動のたびにランダム生成する（＝再起動でセッションが切れる）。
// 既定値をソースに書くと、それは「共有された秘密」になってしまう。
const SECRET = process.env.RPA_LAB_SECRET || crypto.randomBytes(32).toString('hex');

function sign(payload) {
  return crypto.createHmac('sha256', SECRET).update(payload).digest('base64url');
}

export function issueToken(user) {
  const body = Buffer.from(
    JSON.stringify({ sub: user.id, exp: Date.now() + TTL_MS })
  ).toString('base64url');
  return `${body}.${sign(body)}`;
}

export function verifyToken(token) {
  if (!token || !token.includes('.')) return null;
  const [body, sig] = token.split('.');
  const expected = sign(body);
  if (sig.length !== expected.length) return null;
  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return null;
  let claims;
  try {
    claims = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
  } catch {
    return null;
  }
  if (!claims.exp || claims.exp < Date.now()) return null;
  const user = USERS.find((u) => u.id === claims.sub);
  if (!user) return null;
  return { user, expiresAt: claims.exp };
}

export function readCookies(req) {
  if (req.cookies) return req.cookies; // Vercel が入れてくれる
  const raw = req.headers?.cookie || '';
  return Object.fromEntries(
    raw
      .split(';')
      .map((p) => p.trim())
      .filter(Boolean)
      .map((p) => {
        const i = p.indexOf('=');
        return [p.slice(0, i), decodeURIComponent(p.slice(i + 1))];
      })
  );
}

export function setSessionCookie(res, token) {
  const secure = process.env.VERCEL ? '; Secure' : '';
  res.setHeader(
    'Set-Cookie',
    `${COOKIE}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${TTL_MS / 1000}${secure}`
  );
}

export function clearSessionCookie(res) {
  res.setHeader('Set-Cookie', `${COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`);
}

/** 認証必須のハンドラを包む。未認証なら 401 を返して終わり。 */
export function requireSession(req, res) {
  const session = verifyToken(readCookies(req)[COOKIE]);
  if (!session) {
    res.statusCode = 401;
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.end(JSON.stringify({ error: 'unauthenticated', message: 'ログインが必要です' }));
    return null;
  }
  return session;
}

export const COOKIE_NAME = COOKIE;
export const SESSION_TTL_MS = TTL_MS;

// ---- ログイン試行のレート制限（メモリ内） -------------------------------
const attempts = new Map();
const MAX_ATTEMPTS = 5;
const LOCK_MS = 60 * 1000;

export function checkLock(email) {
  const a = attempts.get(email);
  if (a && a.lockedUntil > Date.now()) {
    return Math.ceil((a.lockedUntil - Date.now()) / 1000);
  }
  return 0;
}

export function recordFailure(email) {
  const a = attempts.get(email) || { count: 0, lockedUntil: 0 };
  a.count += 1;
  if (a.count >= MAX_ATTEMPTS) {
    a.lockedUntil = Date.now() + LOCK_MS;
    a.count = 0;
  }
  attempts.set(email, a);
}

export function recordSuccess(email) {
  attempts.delete(email);
}
