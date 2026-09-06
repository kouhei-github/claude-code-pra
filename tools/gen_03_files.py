# -*- coding: utf-8 -*-
"""単元03: 命名も置き場所もバラバラな「受信箱」フォルダを生成する。"""
import random
from pathlib import Path

from openpyxl import Workbook

BASE = Path(__file__).resolve().parents[1] / "units/03-file-organization/data"
INBOX = BASE / "受信箱"
random.seed(303)

# (相対パス, 中身の要約) — 拡張子と実体を一致させる
TEXT_FILES = [
    "見積書_ミナト製作所_最新.md",
    "見積書_ミナト製作所_最新(2).md",
    "見積り ミナト製作所 20260412.md",
    "議事録0415.md",
    "議事録_20260422_ミナト製作所.md",
    "MTGメモ  4-28.md",
    "meeting-notes-2026-05-06.md",
    "ヒアリングシート_アオイ物流.md",
    "提案書ドラフト_v1.md",
    "提案書ドラフト_v2_修正版.md",
    "提案書ドラフト_v2_修正版_最終.md",
    "提案書ドラフト_v2_修正版_最終_FIX.md",
    "sakura-foods 要件.md",
    "【至急】サクラフーズ様_質問回答.md",
    "無題ドキュメント.md",
    "コピー ～ 契約条件メモ.md",
    "IMG_20260518_notes.md",
    "todo.md",
    "アオイ物流_キックオフ_議事録.md",
    "20260601_週報.md",
    "週報 6月8日.md",
    "週報(6月15日).md",
    "screenshot説明.md",
    "PoC結果_ミナト.md",
    "PoC結果_ミナト_rev.md",
    "先方から届いたやつ.md",
    "sakurafoods_契約書_確認事項.md",
    "名刺メモ.md",
    "経費まとめ_4月.md",
    "aoi_logistics_ROI試算メモ.md",
]

CSV_FILES = {
    "リード一覧.csv": "会社名,担当者,メール,流入元,登録日\nミナト製作所,佐々木,sasaki@example.co.jp,展示会,2026-04-02\nアオイ物流,小林,kobayashi@example.co.jp,Web,2026-04-19\nサクラフーズ,森,mori@example.co.jp,紹介,2026-05-11\n",
    "リード一覧 のコピー.csv": "会社名,担当者,メール,流入元,登録日\nミナト製作所,佐々木,sasaki@example.co.jp,展示会,2026-04-02\nアオイ物流,小林,kobayashi@example.co.jp,Web,2026-04-19\nサクラフーズ,森,mori@example.co.jp,紹介,2026-05-11\n",
    "export (3).csv": "id,name,amount\n1,ミナト製作所,3600000\n2,アオイ物流,1200000\n3,サクラフーズ,2400000\n",
}

XLSX_FILES = [
    "見積計算_ミナト.xlsx",
    "見積計算_ミナト 最新版.xlsx",
    "ROI試算_アオイ物流.xlsx",
    "案件管理表.xlsx",
    "案件管理表_旧.xlsx",
    "サクラフーズ_ライセンス数.xlsx",
]

NOTE_BODY = """# {title}

作成日: {date}
関連先: {client}

## 内容
{body}

## 次アクション
- [ ] {action}
"""

CLIENTS = ["ミナト製作所", "アオイ物流", "サクラフーズ", "（未定）"]
BODIES = [
    "先方の要望と現行機能のギャップを整理した。API連携が最大の論点。",
    "予算枠は年間400万円程度。決裁は9月の役員会。",
    "現場のExcel運用をどこまで残すかで意見が割れている。",
    "セキュリティ質問票への回答が必要。情シスが窓口。",
    "PoCは2週間。成功基準は登録作業時間の30%削減。",
]
ACTIONS = [
    "見積を再提出する",
    "開発にAPI連携の実現可能性を確認する",
    "セキュリティ質問票に回答する",
    "議事録を先方に送付して合意を取る",
    "次回打合せを設定する",
]

CONVENTION = """# ファイル命名・配置ルール（営業部）

## フォルダ構成
```
顧客/
  <顧客名>/
    01_商談/     … 議事録・ヒアリングシート
    02_提案/     … 提案書・見積・ROI試算
    03_契約/     … 契約書・条件メモ
    04_導入/     … キックオフ・PoC・要件
社内/
  週報/
  経費/
_アーカイブ/      … 重複・旧版・不要ファイル
```

## ファイル名
`YYYYMMDD_<顧客名>_<種別>_v<版数>.<拡張子>`

- 日付は必ず 8 桁（例: 20260415）。ファイル内に日付があればそれを優先する。
- 顧客名は正式名称に統一する（`sakura-foods` / `サクラフーズ` → `サクラフーズ`）。
- 種別は次から選ぶ: 議事録 / ヒアリング / 提案書 / 見積 / ROI試算 / 契約 / PoC / 週報 / 経費
- 版数は v1 から。`最終`『FIX』『修正版』などの語は使わない。
- 「コピー ～」「(2)」「のコピー」等は重複候補。内容が同一なら `_アーカイブ/` へ。

## やってはいけないこと
- 元ファイルを **削除しない**（アーカイブへ移動する）
- 中身を見ずにファイル名だけで顧客を推測しない
"""


def main():
    INBOX.mkdir(parents=True, exist_ok=True)
    dates = ["2026-04-12", "2026-04-15", "2026-04-22", "2026-04-28", "2026-05-06",
             "2026-05-11", "2026-05-18", "2026-06-01", "2026-06-08", "2026-06-15"]
    for i, name in enumerate(TEXT_FILES):
        client = next((c for c in CLIENTS[:3] if c in name), None)
        if client is None:
            for key, c in [("sakura", "サクラフーズ"), ("aoi", "アオイ物流"),
                           ("ミナト", "ミナト製作所"), ("サクラ", "サクラフーズ")]:
                if key.lower() in name.lower():
                    client = c
                    break
        client = client or random.choice(CLIENTS)
        (INBOX / name).write_text(
            NOTE_BODY.format(title=Path(name).stem, date=dates[i % len(dates)],
                             client=client, body=BODIES[i % len(BODIES)],
                             action=ACTIONS[i % len(ACTIONS)]),
            encoding="utf-8")

    for name, body in CSV_FILES.items():
        (INBOX / name).write_text(body, encoding="utf-8")

    for name in XLSX_FILES:
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["項目", "数量", "単価", "金額"])
        for r in range(3):
            q, u = random.randint(1, 30), random.choice([8000, 120000, 360000])
            ws.append([f"項目{r + 1}", q, u, q * u])
        wb.save(INBOX / name)

    # 一部はサブフォルダに入っている（階層も揃っていない）
    sub = INBOX / "あとで整理"
    sub.mkdir(exist_ok=True)
    for name in ["古い提案書.md", "使うかも.md", "20260320_ミナト製作所_議事録.md"]:
        (sub / name).write_text(NOTE_BODY.format(
            title=Path(name).stem, date="2026-03-20", client="ミナト製作所",
            body=BODIES[0], action=ACTIONS[0]), encoding="utf-8")

    (BASE / "命名規則.md").write_text(CONVENTION, encoding="utf-8")
    n = sum(1 for _ in INBOX.rglob("*") if _.is_file())
    print(f"wrote {n} files under {INBOX}")


if __name__ == "__main__":
    main()
