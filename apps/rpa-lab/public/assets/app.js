// 画面共通の処理。ビルド不要のプレーンな ES モジュール。
export const yen = (n) => '¥' + Number(n || 0).toLocaleString('ja-JP');
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

export const BADGE = {
  下書き: 'draft', 申請中: 'pending', 承認済: 'approved', 差戻し: 'returned', 出荷済: 'shipped',
};
export const badge = (status) =>
  `<span class="badge ${BADGE[status] || 'draft'}" data-status="${status}">${status}</span>`;

/** 401 を受けたらログイン画面へ戻す。RPA 側は「セッション切れ」を検知できる。 */
export async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (res.status === 401 && !path.startsWith('/api/auth')) {
    location.href = '/?expired=1';
    throw new Error('session expired');
  }
  const text = await res.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
  if (!res.ok) {
    const err = new Error(data.message || `HTTP ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export function toast(message, kind = '') {
  let host = $('#toasts');
  if (!host) {
    host = document.createElement('div');
    host.id = 'toasts';
    document.body.appendChild(host);
  }
  const el = document.createElement('div');
  el.className = `toast ${kind}`.trim();
  el.setAttribute('role', 'status');
  el.dataset.testid = 'toast';
  el.textContent = message;
  host.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

/** 二重送信防止。処理中はボタンを無効化してラベルを差し替える。 */
export async function withBusy(button, label, fn) {
  const original = button.textContent;
  button.disabled = true;
  button.dataset.busy = '1';
  button.textContent = label;
  try {
    return await fn();
  } finally {
    button.disabled = false;
    delete button.dataset.busy;
    button.textContent = original;
  }
}

export function debounce(fn, ms = 350) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

export function modal({ title, body, confirmLabel = 'OK', confirmClass = 'btn', onConfirm }) {
  const wrap = document.createElement('div');
  wrap.className = 'backdrop';
  wrap.dataset.testid = 'modal';
  wrap.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true" aria-label="${title}">
      <div class="modal-head">
        <h3>${title}</h3>
        <button type="button" aria-label="閉じる" data-testid="modal-close">&times;</button>
      </div>
      <div class="modal-body"></div>
      <div class="modal-foot">
        <button type="button" class="btn secondary" data-testid="modal-cancel">キャンセル</button>
        <button type="button" class="${confirmClass}" data-testid="modal-confirm">${confirmLabel}</button>
      </div>
    </div>`;
  $('.modal-body', wrap).append(body);
  const close = () => wrap.remove();
  $('[data-testid=modal-close]', wrap).onclick = close;
  $('[data-testid=modal-cancel]', wrap).onclick = close;
  $('[data-testid=modal-confirm]', wrap).onclick = async (e) => {
    const ok = await onConfirm(wrap, e.currentTarget);
    if (ok !== false) close();
  };
  wrap.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  document.body.appendChild(wrap);
  const firstInput = wrap.querySelector('input,textarea,select');
  (firstInput || $('[data-testid=modal-confirm]', wrap)).focus();
  return { el: wrap, close };
}

const NAV = [
  ['/dashboard', 'ダッシュボード'],
  ['/orders', '受注一覧'],
  ['/order-new', '受注登録'],
  ['/approvals', '承認'],
  ['/reports', 'レポート'],
];

/** 各ページの先頭で呼ぶ。未ログインならログイン画面へ飛ばす。 */
export async function boot(current) {
  let me;
  try {
    me = await api('/api/auth');
  } catch {
    location.href = '/?expired=1';
    throw new Error('unauthenticated');
  }

  const bar = document.createElement('header');
  bar.className = 'topbar';
  bar.innerHTML = `
    <div class="topbar-in">
      <div class="logo"><span class="mark">A</span>Altair 受注管理 <span class="env-tag">PRACTICE</span></div>
      <nav class="main">${NAV.map(
        ([href, label]) =>
          `<a href="${href}" data-testid="nav-${href.slice(1)}"${
            href === current ? ' aria-current="page"' : ''
          }>${label}</a>`
      ).join('')}</nav>
      <div class="topbar-right">
        <span class="who" data-testid="current-user"><b>${me.user.name}</b> / ${me.user.dept}</span>
        <button class="linkbtn" type="button" data-testid="logout">ログアウト</button>
      </div>
    </div>`;
  document.body.prepend(bar);
  $('[data-testid=logout]', bar).onclick = async () => {
    await api('/api/auth', { method: 'DELETE' });
    location.href = '/';
  };

  const foot = document.createElement('div');
  foot.className = 'foot';
  foot.innerHTML =
    'RPA 練習用のダミーシステムです。実在の企業・個人とは関係ありません。' +
    ' データを初期化するには <code>DELETE /api/meta?reset=1</code>。';
  document.body.appendChild(foot);

  // ログイン後 1 回だけ出るお知らせ。閉じるまで操作の邪魔になる（RPA の練習）
  if (sessionStorage.getItem('rpa_lab_notice') !== 'seen') {
    sessionStorage.setItem('rpa_lab_notice', 'seen');
    const body = document.createElement('div');
    body.innerHTML = `
      <p style="margin-top:0">2026年10月のメンテナンス予定についてお知らせします。</p>
      <p>10月18日(日) 2:00〜5:00 の間、受注登録および承認機能を停止いたします。
         お手数ですが、当該時間帯を避けてご利用ください。</p>
      <p style="margin-bottom:0;color:var(--muted);font-size:12.5px">
         ※ これは練習用のお知らせです。ログインのたびに1回だけ表示されます。</p>`;
    modal({
      title: 'システムからのお知らせ',
      body,
      confirmLabel: '確認しました',
      onConfirm: () => true,
    });
  }

  return me.user;
}
