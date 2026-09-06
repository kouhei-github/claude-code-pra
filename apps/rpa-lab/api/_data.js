// 練習用の疑似業務データ。決定論的に生成するので、どの環境でも同じ内容になる。
// 実在の企業・個人とは一切関係ありません。

/** xorshift32 — シード固定の擬似乱数 */
function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

// 練習用アカウント。パスワードは環境変数で上書きできる。
// 既定値をあえて `demo` にしてあるのは、強そうな文字列を書くと
// 「守るべき秘密」に見えてしまうため。ここに秘密は置かない。
export const DEFAULT_PASSWORD = 'demo';

export const USERS = [
  {
    id: 'u-tanaka',
    email: process.env.RPA_SALES_EMAIL || 'tanaka@altair.example.co.jp',
    password: process.env.RPA_SALES_PASSWORD || DEFAULT_PASSWORD,
    name: '田中 健',
    dept: '営業本部 西日本チーム',
    roles: ['sales'],
  },
  {
    id: 'u-okochi',
    email: process.env.RPA_APPROVER_EMAIL || 'okochi@altair.example.co.jp',
    password: process.env.RPA_APPROVER_PASSWORD || DEFAULT_PASSWORD,
    name: '大河内 篤',
    dept: '営業本部',
    roles: ['sales', 'approver'],
  },
];

export const PRODUCTS = [
  { code: 'P-001', name: 'スタンダードプラン(年間)', price: 120000, category: 'サブスク' },
  { code: 'P-002', name: 'プロプラン(年間)', price: 360000, category: 'サブスク' },
  { code: 'P-003', name: 'エンタープライズ(年間)', price: 1200000, category: 'サブスク' },
  { code: 'P-101', name: '導入支援パッケージ', price: 250000, category: 'プロフェッショナルサービス' },
  { code: 'P-102', name: '追加ユーザーライセンス', price: 8000, category: 'サブスク' },
  { code: 'P-103', name: 'オンサイト研修(1日)', price: 180000, category: 'プロフェッショナルサービス' },
  { code: 'P-201', name: 'APIアドオン', price: 45000, category: 'アドオン' },
  { code: 'P-202', name: 'SSOアドオン', price: 60000, category: 'アドオン' },
];

export const CUSTOMERS = [
  '株式会社ミナト製作所', 'アオイ物流株式会社', 'サクラフーズ株式会社',
  '有限会社トライアングル設計', '株式会社ノースゲート商事', '株式会社ひかり調剤',
  '東雲テクノロジー株式会社', '株式会社みらい教育出版', '九重ホールディングス株式会社',
  '株式会社カワセミ電機', '株式会社リバーサイド不動産', '合同会社アンカーワークス',
  '株式会社ハルカゼ運輸', '株式会社セイリング化成', '株式会社オリオン印刷',
  '株式会社みなみ野スポーツ', '株式会社ケヤキ総研', '株式会社フジノ精機',
  '株式会社まほろば観光', '株式会社シリウス人材', '株式会社アカツキ食品',
  '株式会社光和メディカル', '株式会社トナリノ工務店', '株式会社ブルーポート海運',
  '株式会社ユメミヤ商店', '株式会社コトブキ精密', '株式会社セントラル警備社',
  '株式会社ハナミズキ製菓', '株式会社レイクサイド観光', '株式会社ゼニス金属',
].map((name, i) => ({ id: `C-${String(i + 1).padStart(3, '0')}`, name }));

const REPS = ['田中 健', '伊藤 さくら', '山田 太郎', '佐藤 花子', '鈴木 一郎'];
const STATUSES = ['下書き', '申請中', '承認済', '差戻し', '出荷済'];

/** 受注120件。ID・内容ともに決定論的。 */
export const ORDERS = (() => {
  const rand = rng(20260913);
  const pick = (arr) => arr[Math.floor(rand() * arr.length)];
  const out = [];
  for (let i = 0; i < 120; i++) {
    const customer = pick(CUSTOMERS);
    const lineCount = 1 + Math.floor(rand() * 3);
    const lines = [];
    for (let j = 0; j < lineCount; j++) {
      const p = pick(PRODUCTS);
      const qty = pick([1, 1, 1, 2, 3, 5, 10, 20, 50]);
      lines.push({ code: p.code, name: p.name, qty, unitPrice: p.price, amount: qty * p.price });
    }
    const amount = lines.reduce((s, l) => s + l.amount, 0);
    // 2026-04-01 起点で最大 180 日
    const day = Math.floor(rand() * 180);
    const orderedAt = new Date(Date.UTC(2026, 3, 1) + day * 86400000);
    const dueAt = new Date(orderedAt.getTime() + (14 + Math.floor(rand() * 45)) * 86400000);
    // 申請中を 22 件ほど作る（承認演習用）
    const status = i < 22 ? '申請中' : pick(STATUSES);
    out.push({
      id: `SO-2026-${String(1000 + i)}`,
      customerId: customer.id,
      customer: customer.name,
      rep: pick(REPS),
      amount,
      lines,
      status,
      orderedAt: orderedAt.toISOString().slice(0, 10),
      dueAt: dueAt.toISOString().slice(0, 10),
      note: '',
      history: [{ at: orderedAt.toISOString(), by: 'seed', action: '作成' }],
    });
  }
  return out.sort((a, b) => (a.orderedAt < b.orderedAt ? 1 : -1));
})();

export function summarize(orders) {
  const by = (s) => orders.filter((o) => o.status === s);
  return {
    total: orders.length,
    totalAmount: orders.reduce((s, o) => s + o.amount, 0),
    pending: by('申請中').length,
    approved: by('承認済').length,
    returned: by('差戻し').length,
    shipped: by('出荷済').length,
    draft: by('下書き').length,
    topCustomers: Object.entries(
      orders.reduce((m, o) => ((m[o.customer] = (m[o.customer] || 0) + o.amount), m), {})
    )
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, amount]) => ({ name, amount })),
  };
}
