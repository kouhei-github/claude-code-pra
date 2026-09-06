// 受注データの可変ストア（プロセス内メモリ）。
//
// Vercel のサーバーレス環境ではインスタンスが入れ替わると初期状態に戻る。
// 練習台としてはそれで構わない（むしろ「途中で状態が消えても壊れないRPA」を
// 書く練習になる）が、腰を据えて演習するときは `npm run dev` のローカル実行を勧める。
import { ORDERS, PRODUCTS, CUSTOMERS, summarize } from './_data.js';

const clone = (v) => JSON.parse(JSON.stringify(v));

let orders = clone(ORDERS);
let seq = 2000;
const reportJobs = new Map();

export function resetAll() {
  orders = clone(ORDERS);
  seq = 2000;
  reportJobs.clear();
}

export function listOrders({ q = '', status = '', page = 1, perPage = 20, sort = 'orderedAt' } = {}) {
  const needle = String(q).trim().toLowerCase();
  let rows = orders;
  if (needle) {
    rows = rows.filter(
      (o) =>
        o.id.toLowerCase().includes(needle) ||
        o.customer.toLowerCase().includes(needle) ||
        o.rep.toLowerCase().includes(needle)
    );
  }
  if (status) rows = rows.filter((o) => o.status === status);
  rows = [...rows].sort((a, b) => {
    if (sort === 'amount') return b.amount - a.amount;
    if (sort === 'id') return a.id < b.id ? -1 : 1;
    return a.orderedAt < b.orderedAt ? 1 : -1;
  });

  const total = rows.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const p = Math.min(Math.max(1, Number(page) || 1), totalPages);
  return {
    rows: rows.slice((p - 1) * perPage, p * perPage).map(({ lines, history, ...rest }) => rest),
    page: p,
    perPage,
    total,
    totalPages,
  };
}

export function getOrder(id) {
  return orders.find((o) => o.id === id) || null;
}

export function createOrder({ customerId, rep, dueAt, lines, note }, user) {
  const customer = CUSTOMERS.find((c) => c.id === customerId);
  if (!customer) return { error: '顧客が見つかりません（customerId）' };
  if (!Array.isArray(lines) || lines.length === 0) return { error: '明細が1行もありません' };
  if (!dueAt || !/^\d{4}-\d{2}-\d{2}$/.test(dueAt)) return { error: '納期は YYYY-MM-DD 形式で指定してください' };

  const built = [];
  for (const l of lines) {
    const p = PRODUCTS.find((x) => x.code === l.code);
    if (!p) return { error: `商品コードが不正です: ${l.code}` };
    const qty = Number(l.qty);
    if (!Number.isInteger(qty) || qty < 1) return { error: `数量が不正です: ${l.code}` };
    built.push({ code: p.code, name: p.name, qty, unitPrice: p.price, amount: qty * p.price });
  }

  seq += 1;
  const order = {
    id: `SO-2026-${seq}`,
    customerId: customer.id,
    customer: customer.name,
    rep: rep || user.name,
    amount: built.reduce((s, l) => s + l.amount, 0),
    lines: built,
    status: '申請中',
    orderedAt: new Date().toISOString().slice(0, 10),
    dueAt,
    note: note || '',
    history: [{ at: new Date().toISOString(), by: user.name, action: '作成・申請' }],
  };
  orders.unshift(order);
  return { order };
}

export function decideOrder(id, decision, reason, user) {
  const order = getOrder(id);
  if (!order) return { error: '受注が見つかりません' };
  if (order.status !== '申請中') return { error: `ステータスが「${order.status}」のため承認操作できません` };
  if (!user.roles.includes('approver')) return { error: '承認権限がありません', status: 403 };
  if (decision === 'reject' && String(reason || '').trim().length < 10) {
    return { error: '差戻しには10文字以上の理由が必要です' };
  }
  order.status = decision === 'approve' ? '承認済' : '差戻し';
  order.note = reason || order.note;
  order.history.push({
    at: new Date().toISOString(),
    by: user.name,
    action: decision === 'approve' ? '承認' : '差戻し',
    reason: reason || '',
  });
  return { order };
}

export function summary() {
  return summarize(orders);
}

// ---- 月次レポート（擬似的な非同期ジョブ） -------------------------------
export function startReport(month, user) {
  if (!/^\d{4}-\d{2}$/.test(String(month || ''))) {
    return { error: '対象月は YYYY-MM 形式で指定してください' };
  }
  const id = `job_${Math.random().toString(36).slice(2, 10)}`;
  reportJobs.set(id, {
    id,
    month,
    by: user.name,
    startedAt: Date.now(),
    // 3.5秒かかる想定。ポーリングしないと取れない
    readyAt: Date.now() + 3500,
  });
  return { jobId: id };
}

export function pollReport(id) {
  const job = reportJobs.get(id);
  if (!job) return { error: 'ジョブが見つかりません' };
  if (Date.now() < job.readyAt) {
    const pct = Math.min(
      95,
      Math.round(((Date.now() - job.startedAt) / (job.readyAt - job.startedAt)) * 100)
    );
    return { state: 'running', progress: pct };
  }
  return { state: 'done', progress: 100, downloadUrl: `/api/reports?job=${id}&download=1` };
}

export function renderReportCsv(id) {
  const job = reportJobs.get(id);
  if (!job) return null;
  const rows = orders.filter((o) => o.orderedAt.startsWith(job.month));
  const head = '受注番号,顧客名,担当者,受注日,納期,金額,ステータス';
  const body = rows
    .map((o) => [o.id, o.customer, o.rep, o.orderedAt, o.dueAt, o.amount, o.status].join(','))
    .join('\n');
  return `${head}\n${body}\n`;
}
