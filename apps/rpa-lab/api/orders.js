// GET   /api/orders?q=&status=&page=&perPage=&sort=   → 一覧（サーバ側で検索・絞り込み・ページ送り）
// GET   /api/orders?id=SO-2026-1000                   → 1件（明細・履歴つき）
// POST  /api/orders                                    → 受注を作成して申請中にする
// PATCH /api/orders  { id, decision, reason }          → 承認 / 差戻し（approver ロールのみ）
import { requireSession } from './_auth.js';
import { json, latency, readBody, query } from './_http.js';
import { listOrders, getOrder, createOrder, decideOrder } from './_store.js';

export default async function handler(req, res) {
  const session = requireSession(req, res);
  if (!session) return;
  const user = session.user;
  const q = query(req);

  if (req.method === 'GET') {
    await latency();
    if (q.id) {
      const order = getOrder(q.id);
      if (!order) return json(res, 404, { error: 'not_found', message: '受注が見つかりません' });
      return json(res, 200, { order });
    }
    return json(res, 200, listOrders({
      q: q.q, status: q.status, page: q.page, perPage: q.perPage, sort: q.sort,
    }));
  }

  if (req.method === 'POST') {
    await latency(500, 1100); // 登録は重い処理、という前提
    const body = await readBody(req);
    const result = createOrder(body, user);
    if (result.error) return json(res, 422, { error: 'validation_error', message: result.error });
    return json(res, 201, { order: result.order });
  }

  if (req.method === 'PATCH') {
    await latency(400, 900);
    const { id, decision, reason } = await readBody(req);
    if (!['approve', 'reject'].includes(decision)) {
      return json(res, 422, { error: 'validation_error', message: 'decision は approve か reject' });
    }
    const result = decideOrder(id, decision, reason, user);
    if (result.error) {
      return json(res, result.status || 422, { error: 'rejected', message: result.error });
    }
    return json(res, 200, { order: result.order });
  }

  return json(res, 405, { error: 'method_not_allowed' });
}
