# -*- coding: utf-8 -*-
"""単元02(プロンプト設計) / 09(標準コンテキスト) / 11(定期実行) の素材を生成する。"""
import datetime as dt
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
HEAD = PatternFill("solid", fgColor="1F3864")
HF = Font(bold=True, color="FFFFFF")
random.seed(2911)


def styled(ws, cols, widths):
    ws.append(cols)
    for c in ws[1]:
        c.fill, c.font = HEAD, HF
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "A2"


# ======================================================================
# 単元02: プロンプト設計
# ======================================================================
BAD_PROMPTS = """# 現場で実際に投げられた「雑なプロンプト」集

そのままでは望んだ成果物が返ってこない依頼を10件集めた。
単元02では、この1件ずつを **Task / Context / Format / Constraints** の4要素に
分解して書き直し、`プロンプト評価シート.xlsx` に記録する。

---

1. 「この売上データ、いい感じにまとめて」

2. 「競合調査して」

3. 「議事録つくって」

4. 「エラー直して」

5. 「提案書のたたき台お願い」

6. 「顧客リストを分析して、来月アプローチすべき先を教えて」

7. 「このコード、レビューして」

8. 「先週の問い合わせ、傾向ある？」

9. 「請求書のフォーマット直しといて」

10. 「新機能のリリースノート書いて」

---

## 補足: この会社の前提（書き直すときに使える背景情報）

- 会社: 株式会社アルタイル（SaaS「Altair CRM」を提供、社員240名）
- 読み手は多くの場合、**部長以上**（数字と結論を先に読みたい人たち）
- 定例は毎週月曜10:00。資料は前営業日の17:00までに共有する慣習
- 提案書は A4 で 6〜10 ページ、必ず「課題 → 打ち手 → 費用 → 効果 → 進め方」の順
- コードは TypeScript + React。レビュー観点は「型安全」「テスト有無」「命名」
- リリースノートは日本語・英語の2言語、ユーザー影響のある変更のみ
"""

RUBRIC = """# 良いプロンプトの4要素（評価基準）

| 要素 | 問い | 満点の状態 |
|---|---|---|
| **Task（依頼）** | 何をしてほしいのか、動詞で書けているか | 「〜を作る」「〜を比較する」「〜を検出する」と一意に読める |
| **Context（文脈）** | 誰のため / 何の判断のため / どのファイルを見るのか | 読み手・目的・入力ファイルのパスが書かれている |
| **Format（形式）** | 何が、どのファイル形式で、どこに出るのか | 出力パス・形式・章立て・行数/枚数まで指定されている |
| **Constraints（制約）** | やってはいけないこと、守るべきルール、判断基準 | 禁止事項・上限・優先順位・不明時の振る舞いが書かれている |

各要素 0〜3 点で採点する。

- 0: 記述なし
- 1: 触れているが曖昧（「わかりやすく」「いい感じに」）
- 2: 具体的だが抜けがある
- 3: そのまま実行でき、成果物の合否を判定できる

**合格ライン: 合計 10 点以上、かつ Format が 2 点以上。**

## 4要素が揃っているかの自己チェック
- [ ] このプロンプトだけを新入社員に渡して、同じ成果物が出てくるか
- [ ] 「できました」と言われたとき、合否を判定できるか
- [ ] 判断に迷ったときにどうしてほしいか書いてあるか
- [ ] 触ってほしくないファイル・やってほしくない操作を書いたか
"""


def unit02():
    base = ROOT / "units/02-prompt-design/data"
    base.mkdir(parents=True, exist_ok=True)
    (base / "雑なプロンプト集.md").write_text(BAD_PROMPTS, encoding="utf-8")
    (base / "評価基準.md").write_text(RUBRIC, encoding="utf-8")

    wb = Workbook()
    ws = wb.active
    ws.title = "プロンプト評価"
    styled(ws, ["No", "元のプロンプト", "書き直したプロンプト", "Task", "Context",
                "Format", "Constraints", "合計", "合否", "実行して分かったこと"],
           [5, 34, 60, 8, 9, 9, 12, 8, 8, 44])
    originals = [
        "この売上データ、いい感じにまとめて", "競合調査して", "議事録つくって", "エラー直して",
        "提案書のたたき台お願い", "顧客リストを分析して、来月アプローチすべき先を教えて",
        "このコード、レビューして", "先週の問い合わせ、傾向ある？",
        "請求書のフォーマット直しといて", "新機能のリリースノート書いて",
    ]
    for i, o in enumerate(originals, start=1):
        ws.append([i, o, "", None, None, None, None,
                   f"=SUM(D{i + 1}:G{i + 1})",
                   f'=IF(AND(H{i + 1}>=10,F{i + 1}>=2),"合格","要修正")', ""])
    dv = DataValidation(type="list", formula1='"0,1,2,3"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add("D2:G11")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    ws2 = wb.create_sheet("採点基準")
    styled(ws2, ["要素", "0点", "1点", "2点", "3点"], [16, 26, 30, 30, 40])
    for row in [
        ["Task", "何をするか書いていない", "動詞が曖昧（まとめる・見る）",
         "動詞は明確だが対象範囲が曖昧", "動詞・対象・完了条件が一意"],
        ["Context", "背景なし", "読み手だけ書いてある",
         "読み手と目的はある。入力が不明確", "読み手・目的・入力ファイルパスが揃う"],
        ["Format", "指定なし", "「表で」程度", "形式と出力先はある。粒度が不明",
         "出力パス・形式・章立て・分量まで指定"],
        ["Constraints", "指定なし", "「丁寧に」等の心構えのみ",
         "禁止事項がいくつかある", "禁止事項・上限・不明時の振る舞いが明記"],
    ]:
        ws2.append(row)
    for r in ws2.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    p = base / "プロンプト評価シート.xlsx"
    wb.save(p)
    print("wrote", p)


# ======================================================================
# 単元09: 標準コンテキスト（CLAUDE.md）
# ======================================================================
STYLE_GUIDE = """# 株式会社アルタイル 文章スタイルガイド（社外文書）

## 基本
- 常体は使わない。すべて敬体（です・ます）。
- 1文は 60 字以内を目安にする。
- 数字は半角。3桁区切りのカンマを入れる（例: 1,234,567円）。
- 単位は「円（税抜）」「名」「件」「%」。税込・税抜は必ず明記する。
- 日付は「2026年10月15日」形式。社内資料は `2026-10-15` を許容する。

## 用語
- 自社を指すときは「弊社」。相手は「貴社」（メールでは「御社」）。
- 製品名は必ず **Altair CRM**（Altair、アルタイルCRM は不可）。
- 「ユーザー」＝製品を使う人、「顧客」＝契約している企業。混同しない。

## 禁止表現
| 使わない | 使う |
|---|---|
| 値上げ | 価格改定 |
| ご了承ください | ご理解いただけますと幸いです |
| 弊社では〜させていただきます（連続） | 1通に1回まで |
| AI が / Claude が | （主体は必ず自社。ツール名は社外文書に出さない） |
| 絶対に / 必ず〜できます | 断定を避け「〜を想定しています」 |

## 構成
社外向け提案書は必ず次の順序にする。
1. 課題認識 2. ご提案の全体像 3. 費用 4. 期待効果 5. 進め方 6. 体制

## 数字の扱い
- 実績値と見込値は必ず区別し、見込値には「見込」と付ける。
- 出典のない数字は載せない。社内データは「当社調べ（2026年8月時点）」と注記する。
"""

REPO_NOTE = """# このリポジトリの歩き方（情報の置き場所）

```
units/<単元>/data/      入力。ここは読み取り専用として扱う（書き換えない）
units/<単元>/output/    成果物の出力先。ここだけ書き込んでよい
units/<単元>/solution/  模範解答・お手本のプロンプト
tools/                  教材データの再生成スクリプト
```

## よくある依頼と、そのとき見るファイル
| 依頼 | まず読むもの |
|---|---|
| 売上を集計して | `units/04-.../data/売上データ_2026上期_raw.xlsx` |
| KPIを分析して | `units/07-.../data/KPI_月次_2024-2026.xlsx`（「目標値」シートも） |
| 顧客に送る文章 | `units/09-.../data/文章スタイルガイド.md` を必ず先に読む |
| 経費まわり | `units/05-.../data/経費精算規程.md` |

## 環境
- Python 3.11。Excel は openpyxl、Word は python-docx、PowerPoint は python-pptx。
- 追加ライブラリを入れる前に、既にあるもので済まないか確認する。
- 生成物の文字コードは UTF-8。改行は LF。
"""

BAD_OUTPUT = """# 「惜しい出力」の実例と、なぜダメだったか

CLAUDE.md を書くときの材料。**過去に実際にやり直しになったもの**を集めてある。

---

### 例1: 売上サマリ
> 売上は好調に推移しており、順調に成長しています。

**却下理由**: 数字がない。「好調」の基準もない。
**期待**: 「上期売上は 3億1,200万円（前年同期比 +12.4%）。ただし6月単月は前年割れ（-3.1%）。」

---

### 例2: 顧客への更新案内
> このたび値上げをさせていただくこととなりました。何卒ご了承ください。

**却下理由**: 禁止語（値上げ / ご了承ください）を2つ使用。理由の説明がない。
**期待**: 「価格改定をお願いしております。AI要約機能と監査ログ長期保持の標準提供に伴うものです。」

---

### 例3: 分析レポート
> 解約率が上昇傾向にあると考えられます。原因は複合的と推測されます。

**却下理由**: 「推測されます」で止まっている。次に何をすればいいか分からない。
**期待**: 原因の候補を3つ、それぞれ「このデータで検証できる / できない」を明記する。

---

### 例4: ファイル整理
> 重複ファイル12件を削除しました。

**却下理由**: 削除は禁止（アーカイブへ移動が社内ルール）。復元不能な操作を勝手に実行した。
**期待**: `_アーカイブ/` へ移動し、移動ログを残す。

---

### 例5: Excel加工
> 元のファイルを整形して上書き保存しました。

**却下理由**: 入力ファイルを破壊した。監査時に元データが辿れない。
**期待**: `output/` に新規ファイルとして保存し、入力は触らない。

---

### 例6: 不明点があったとき
> 不明な点があったので、一般的な値を仮定して進めました。

**却下理由**: 仮定した箇所が分からず、成果物全体が信用できなくなる。
**期待**: 仮定した箇所を成果物の冒頭に「前提と未確認事項」として箇条書きで明示する。
"""


def unit09():
    base = ROOT / "units/09-project-context/data"
    base.mkdir(parents=True, exist_ok=True)
    (base / "文章スタイルガイド.md").write_text(STYLE_GUIDE, encoding="utf-8")
    (base / "リポジトリの歩き方.md").write_text(REPO_NOTE, encoding="utf-8")
    (base / "やり直しになった出力の実例.md").write_text(BAD_OUTPUT, encoding="utf-8")

    wb = Workbook()
    ws = wb.active
    ws.title = "社内用語集"
    styled(ws, ["用語", "正しい表記", "誤用されがちな表記", "意味", "使う場面"],
           [22, 22, 30, 52, 22])
    for row in [
        ["製品名", "Altair CRM", "Altair / アルタイルCRM / ALTAIR", "自社の主力SaaS製品", "社外・社内とも"],
        ["ユーザー", "ユーザー", "利用者 / エンドユーザ", "Altair CRM を実際に操作する個人", "社外・社内とも"],
        ["顧客", "顧客", "クライアント / お客様企業", "契約主体である企業", "社内資料"],
        ["MRR", "MRR", "月商 / 月次売上", "月次経常収益。サブスク分のみ。スポット売上は含まない", "経営会議"],
        ["ARR", "ARR", "年商", "MRR × 12", "経営会議"],
        ["解約率", "月次解約率", "チャーン / チャーンレート", "当月解約顧客数 ÷ 前月末顧客数", "経営会議"],
        ["ロゴ", "顧客数", "ロゴ数", "英語資料以外では「顧客数」を使う", "社内資料"],
        ["定着支援", "定着支援プログラム", "オンボーディング支援", "契約後90日間のCS伴走メニュー", "社外・社内とも"],
        ["PS", "プロフェッショナルサービス", "プロサ / PS", "導入支援・研修などの人的サービス", "社内資料"],
        ["FN連携", "Factory Nexus 連携", "基幹連携 / FN", "生産管理 Factory Nexus とのAPI連携機能", "社外・社内とも"],
        ["QBR", "四半期business review", "四半期レビュー", "顧客と行う四半期ごとの振り返り", "社内資料"],
        ["受注", "受注", "クローズ / Won", "契約書締結が完了した状態。内示は受注に含めない", "経営会議"],
        ["パイプライン", "パイプライン", "案件 / 商談", "受注前の案件金額の合計", "経営会議"],
        ["営業本部", "営業本部", "セールス部 / 営業部", "正式な組織名。部ではなく本部", "社外・社内とも"],
        ["CS", "カスタマーサクセス部", "CS部 / サポート", "「サポート」は別組織（テクニカルサポート課）", "社内資料"],
    ]:
        ws.append(row)
    for r in ws.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    ws2 = wb.create_sheet("組織と決裁")
    styled(ws2, ["組織", "責任者", "人数", "決裁範囲", "定例"],
           [26, 16, 8, 30, 26])
    for row in [
        ["営業本部", "大河内 篤（本部長）", 180, "値引き 10% まで", "月曜 10:00 全体"],
        ["└ 東日本チーム", "山田 太郎", 70, "値引き 5% まで", "月曜 11:00"],
        ["└ 西日本チーム", "田中 健", 60, "値引き 5% まで", "月曜 11:00"],
        ["└ パートナー営業", "佐藤 花子", 50, "値引き 5% まで", "火曜 14:00"],
        ["カスタマーサクセス部", "伊藤 さくら（部長）", 60, "定着支援の無償提供 3ヶ月まで", "水曜 15:00"],
        ["テクニカルサポート課", "鈴木 一郎", 25, "―", "毎朝 9:30"],
        ["情報システム部", "佐野 直人", 12, "年間 500万円まで", "木曜 16:00"],
        ["経営企画部", "高橋 みゆき", 10, "―", "月次 経営会議（第2火曜）"],
    ]:
        ws2.append(row)
    for r in ws2.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    p = base / "社内用語集と組織.xlsx"
    wb.save(p)
    print("wrote", p)


# ======================================================================
# 単元11: 定期実行（週次ダイジェスト）
# ======================================================================
DIGEST_FORMAT = """# 週次ダイジェスト フォーマット

毎週月曜 8:00 に、前週分（月〜日）を1枚にまとめて `output/` へ出力する。
読み手は **営業本部長・CS部長・情シス部長**。3分で読み終わる分量にすること。

## 構成（この順序を変えない）

```markdown
# 週次ダイジェスト 2026年 第XX週（M月D日〜M月D日）

## 1. 今週の結論（3行以内）
数字と、それに対する判断を書く。「様子見」も判断として書いてよい。

## 2. 数字
| 指標 | 今週 | 前週 | 増減 | 目標 | 判定 |
（判定は 🟢達成 / 🟡注意 / 🔴未達 のいずれか）

## 3. 動いた案件（上位5件）
金額の大きい順。ステージが変わったものだけ。

## 4. 気をつけるべきこと（3件まで）
サポート・障害・解約リスクから、来週アクションが必要なものだけ。
「特になし」も明記する。

## 5. 先週の宿題の状況
前回ダイジェストの「気をつけるべきこと」がどうなったかを1行ずつ。
```

## 判定のしきい値
| 指標 | 🟢 | 🟡 | 🔴 |
|---|---|---|---|
| 新規受注額（週） | 8,000,000円以上 | 5,000,000〜7,999,999円 | 5,000,000円未満 |
| 初回応答時間（中央値） | 4.0時間以下 | 4.1〜8.0時間 | 8.0時間超 |
| 未解決チケット（P1） | 0件 | 1件 | 2件以上 |
| デプロイ失敗 | 0件 | 1件 | 2件以上 |

## 禁止
- 生データの表をそのまま貼らない（要約する）
- 「引き続き注視します」だけで終わらせない。誰が何をいつまでにやるかを書く
"""


def week_dates(year, week):
    monday = dt.date.fromisocalendar(year, week, 1)
    return [monday + dt.timedelta(days=i) for i in range(7)]


def gen_tickets(path, year, week, p1_count, base_frt):
    cats = ["ログイン/SSO", "レポート表示", "API連携", "データ移行", "請求", "モバイル", "その他"]
    comps = ["ミナト製作所", "アオイ物流", "サクラフーズ", "ノースゲート商事", "東雲テクノロジー",
             "カワセミ電機", "九重ホールディングス", "フジノ精機", "ブルーポート海運", "ゼニス金属"]
    lines = ["チケットID,起票日時,顧客名,カテゴリ,優先度,件名,ステータス,初回応答時間(時間),解決までの時間(時間),担当"]
    days = week_dates(year, week)
    n = random.randint(38, 52)
    for i in range(n):
        d = random.choice(days)
        hh = random.randint(8, 19)
        pri = "P1" if i < p1_count else random.choice(["P2", "P2", "P3", "P3", "P3"])
        status = random.choice(["解決済", "解決済", "解決済", "対応中", "顧客待ち"])
        if pri == "P1" and i < 1:
            status = "対応中"
        frt = round(max(0.2, random.gauss(base_frt, 2.0)), 1)
        ttr = round(frt + random.uniform(1, 40), 1) if status == "解決済" else ""
        cat = random.choice(cats)
        lines.append(
            f"TCK-{year}{week:02d}{i:03d},{d} {hh:02d}:{random.randint(0,59):02d},"
            f"{random.choice(comps)},{cat},{pri},"
            f"{cat}に関するお問い合わせ,{status},{frt},{ttr},"
            f"{random.choice(['鈴木','中村','渡辺','小川'])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def gen_pipeline(path, year, week, won_total):
    comps = ["ミナト製作所", "アオイ物流", "サクラフーズ", "トライアングル設計", "ノースゲート商事",
             "ひかり調剤", "東雲テクノロジー", "みらい教育出版", "カワセミ電機", "ハルカゼ運輸",
             "セイリング化成", "オリオン印刷", "ケヤキ総研", "フジノ精機", "シリウス人材"]
    stages = ["初回商談", "課題ヒアリング", "提案", "見積提示", "最終交渉", "受注", "失注"]
    reps = ["田中 健", "伊藤 さくら", "山田 太郎", "佐藤 花子", "鈴木 一郎"]
    lines = ["案件ID,顧客名,金額(円),ステージ,前週ステージ,確度(%),営業担当,更新日,次アクション"]
    days = week_dates(year, week)
    remaining = won_total
    for i in range(random.randint(16, 22)):
        comp = comps[i % len(comps)]
        prev = random.choice(stages[:5])
        stage = random.choice(stages)
        if stage == "受注" and remaining > 0:
            amt = min(remaining, random.choice([1_200_000, 2_400_000, 3_600_000, 4_800_000]))
            remaining -= amt
        elif stage == "受注":
            stage = random.choice(stages[:5])
            amt = random.choice([1_200_000, 2_400_000, 3_600_000, 7_200_000, 12_000_000])
        else:
            amt = random.choice([1_200_000, 2_400_000, 3_600_000, 7_200_000, 12_000_000])
        prob = {"初回商談": 10, "課題ヒアリング": 20, "提案": 40,
                "見積提示": 60, "最終交渉": 80, "受注": 100, "失注": 0}[stage]
        lines.append(f"OPP-{year}{week:02d}{i:03d},{comp},{amt},{stage},{prev},{prob},"
                     f"{random.choice(reps)},{random.choice(days)},"
                     f"{random.choice(['次回打合せ設定','見積再提出','稟議待ち','セキュリティ質問票回答','―'])}")
    if remaining > 0:
        lines.append(f"OPP-{year}{week:02d}900,{comps[0]},{remaining},受注,最終交渉,100,"
                     f"{reps[0]},{days[4]},―")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def gen_deploys(path, year, week, failures):
    days = week_dates(year, week)
    lines = []
    for i in range(random.randint(9, 14)):
        d = random.choice(days)
        ok = "SUCCESS" if i >= failures else "FAILED"
        dur = random.randint(180, 900)
        svc = random.choice(["altair-api", "altair-web", "altair-worker", "altair-reporting"])
        lines.append(f"{d} {random.randint(9,20):02d}:{random.randint(0,59):02d}:00 "
                     f"[{ok}] {svc} v2026.{week}.{i} duration={dur}s "
                     f"by={random.choice(['ci-bot','h.sano','r.shiraishi'])}"
                     + ("" if ok == "SUCCESS" else "  error=migration timeout on orders table"))
    path.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")


def unit11():
    base = ROOT / "units/11-scheduled-automation/data"
    (base / "週次").mkdir(parents=True, exist_ok=True)
    (base / "ダイジェスト_フォーマット.md").write_text(DIGEST_FORMAT, encoding="utf-8")

    # W35(前週) は落ち着いている / W36(今週) は悪化している → 比較で差分が出る
    for week, p1, frt, won, fails in [(35, 1, 5.0, 9_600_000, 0), (36, 3, 9.4, 4_800_000, 2)]:
        gen_tickets(base / "週次" / f"support_tickets_2026-W{week}.csv", 2026, week, p1, frt)
        gen_pipeline(base / "週次" / f"pipeline_2026-W{week}.csv", 2026, week, won)
        gen_deploys(base / "週次" / f"deploy_log_2026-W{week}.txt", 2026, week, fails)

    # 先週分のダイジェスト（「先週の宿題」を追跡させるため）
    (base / "先週のダイジェスト_2026-W35.md").write_text("""# 週次ダイジェスト 2026年 第35週（8月24日〜8月30日）

## 1. 今週の結論
- 新規受注は 9,600,000円で目標達成（🟢）。ノースゲート商事の追加ライセンスが牽引。
- サポートは平常運転。初回応答時間の中央値は 5.0 時間で 🟡。
- デプロイ失敗ゼロ。リリースは予定どおり。

## 2. 数字
| 指標 | 今週 | 前週 | 増減 | 目標 | 判定 |
|---|---|---|---|---|---|
| 新規受注額 | 9,600,000円 | 8,200,000円 | +1,400,000 | 8,000,000円 | 🟢 |
| 初回応答時間(中央値) | 5.0時間 | 4.6時間 | +0.4 | 4.0時間 | 🟡 |
| 未解決P1 | 1件 | 0件 | +1 | 0件 | 🟡 |
| デプロイ失敗 | 0件 | 1件 | -1 | 0件 | 🟢 |

## 3. 動いた案件（上位5件）
1. ノースゲート商事 12,000,000円 最終交渉 → 受注
2. フジノ精機 7,200,000円 提案 → 見積提示
3. 東雲テクノロジー 3,600,000円 課題ヒアリング → 提案
4. ハルカゼ運輸 2,400,000円 初回商談 → 課題ヒアリング
5. サクラフーズ 2,400,000円 見積提示 → 最終交渉

## 4. 気をつけるべきこと
1. **API連携の問い合わせが先週比で倍増（4→8件）。** 8/28のリリースとの関連を情シスで確認する。担当: 佐野 / 期限: 9/3
2. **カワセミ電機の未解決P1（TCK-2026035011）が3営業日経過。** エスカレーション基準を超えている。担当: 鈴木 / 期限: 9/1
3. 特になし

## 5. 先週の宿題の状況
- レポート表示の遅延 → 8/26のリリースで解消を確認。クローズ。
""", encoding="utf-8")
    print("wrote unit11 materials")


if __name__ == "__main__":
    unit02()
    unit09()
    unit11()
