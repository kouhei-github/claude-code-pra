// GET    /api/meta            → 商品・顧客・サマリ（要ログイン）
// DELETE /api/meta?reset=1    → 練習データを初期状態に戻す（要ログイン）
import { PRODUCTS, CUSTOMERS } from './_data.js';
import { requireSession } from './_auth.js';
import { json, latency, query } from './_http.js';
import { summary, resetAll } from './_store.js';

export default async function handler(req, res) {
  const session = requireSession(req, res);
  if (!session) return;

  if (req.method === 'DELETE' || query(req).reset === '1') {
    resetAll();
    return json(res, 200, { ok: true, message: '練習データを初期状態に戻しました' });
  }

  await latency(150, 400);
  const { password, ...user } = session.user;
  return json(res, 200, { user, products: PRODUCTS, customers: CUSTOMERS, summary: summary() });
}
