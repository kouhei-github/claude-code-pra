// POST /api/reports  { month:"2026-06" }        → 生成ジョブを開始し jobId を返す
// GET  /api/reports?job=<id>                    → 進捗 { state, progress }
// GET  /api/reports?job=<id>&download=1         → 完了後に CSV を返す
//
// 3.5秒かかる非同期ジョブ。押した直後にダウンロードできないので、
// RPA 側にポーリング（待つ）実装を強制する。
import { requireSession } from './_auth.js';
import { json, latency, readBody, query } from './_http.js';
import { startReport, pollReport, renderReportCsv } from './_store.js';

export default async function handler(req, res) {
  const session = requireSession(req, res);
  if (!session) return;
  const q = query(req);

  if (req.method === 'POST') {
    await latency(300, 700);
    const { month } = await readBody(req);
    const r = startReport(month, session.user);
    if (r.error) return json(res, 422, { error: 'validation_error', message: r.error });
    return json(res, 202, r);
  }

  if (req.method === 'GET') {
    if (!q.job) return json(res, 422, { error: 'validation_error', message: 'job を指定してください' });
    const status = pollReport(q.job);
    if (status.error) return json(res, 404, { error: 'not_found', message: status.error });

    if (q.download === '1') {
      if (status.state !== 'done') {
        return json(res, 409, { error: 'not_ready', message: 'レポートはまだ生成中です' });
      }
      const csv = renderReportCsv(q.job);
      res.statusCode = 200;
      res.setHeader('Content-Type', 'text/csv; charset=utf-8');
      res.setHeader('Content-Disposition', `attachment; filename="report_${q.job}.csv"`);
      res.setHeader('Cache-Control', 'no-store');
      return res.end('﻿' + csv); // Excel 対策の BOM
    }
    return json(res, 200, status);
  }

  return json(res, 405, { error: 'method_not_allowed' });
}
