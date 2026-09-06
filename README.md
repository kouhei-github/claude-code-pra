# Claude Code で学ぶ Cowork ユースケース

[Claude Academy](https://academy.claude.com/) の *Introduction to Claude Cowork* が扱う業務ユースケース
（スプレッドシートの整理、文書の統合、文章の量産、ワークフローの自動化、ブラウザ操作）を、
**Claude Code でそのまま実践できる形**に置き換えた12単元の教材です。

Cowork がデスクトップ上のファイルとアプリを相手にするのに対して、Claude Code は
**リポジトリとターミナル**を相手にします。やることは同じですが、
「出力先がパスで決まる」「git で差分が見える」「検証をスクリプトで書ける」という違いがあり、
そこが実務での信頼性の差になります。この教材はその差を体感することを狙っています。

学習サイト（1枚のHTML）: `site/index.html` — Artifact として公開できます。

---

## 特徴

- **架空だが一貫した舞台設定** — SaaS企業「株式会社アルタイル」（製品 `Altair CRM`、社員240名）。
  12単元すべて同じ会社・同じ顧客・同じ数字でつながっています。
- **本物の壊れ方をした実データ** — 表記ゆれ、和暦、全角数字、重複行、二重計上、
  未回答のセキュリティ質問票。「きれいなサンプル」ではありません。
- **正解が検証できる** — 各単元に合格チェックリストと、検証スクリプトを書かせる課題があります。
- **再生成できる** — `python3 tools/generate_all.py` で全データを復元できます（シード固定）。
- **ブラウザにも出る** — 単元13・14 では、同梱の業務システムを Claude Code に操作させます。

## 単元一覧

| # | 単元 | Cowork のユースケース | 主な成果物 | 目安 |
|---|---|---|---|---|
| 01 | [セットアップと最初のタスクループ](units/01-setup-first-loop/) | 作業フォルダと権限モード、最初の依頼 | 週報.md | 25分 |
| 02 | [プロンプト設計](units/02-prompt-design/) | task / context / format / constraints | 書き直し版.md、評価シート.xlsx | 40分 |
| 03 | [ファイル整理と一括リネーム](units/03-file-organization/) | 階層設計・自動仕分け・一括リネーム | 整理計画.md、整理後のフォルダ | 35分 |
| 04 | [スプレッドシートのクリーンアップ](units/04-spreadsheet-cleanup/) | 汚れた表を集計できる状態にする | clean.xlsx（4シート）、verify.py | 45分 |
| 05 | [非構造データを表に変える](units/05-unstructured-to-table/) | 領収書・メモ → 集計できる表 | 経費精算.xlsx | 45分 |
| 06 | [複数文書の統合](units/06-document-synthesis/) | ドキュメント統合・意思決定資料 | 比較表.xlsx、サマリ.md、pptx | 50分 |
| 07 | [データ分析とレポート生成](units/07-data-analysis-report/) | 数字から傾向と示唆を出す | 数値サマリ.xlsx、分析レポート.md、pptx | 50分 |
| 08 | [定型文書の量産](units/08-bulk-document-generation/) | ひな形＋一覧から宛先ごとに生成 | 30通のdocx、送付管理表.xlsx | 45分 |
| 09 | [CLAUDE.md で標準コンテキスト](units/09-project-context/) | グローバル指示・プロジェクト | CLAUDE.md、settings.json | 40分 |
| 10 | [業務を Skill にする](units/10-custom-skill/) | Skill を作る | SKILL.md、月次レポート.md | 50分 |
| 11 | [定期実行の自動化](units/11-scheduled-automation/) | スケジュールタスク | 週次ダイジェスト、cron / Actions | 45分 |
| 12 | [総合演習（サブエージェント並列）](units/12-subagents-capstone/) | 複数成果物をチーム品質に仕上げる | 3社×3成果物＋レビュー | 60分 |
| 13 | [ブラウザ操作と自動ログイン](units/13-browser-login/) | Claude を Chrome に入れて操作させる | 抽出CSV、セレクタ設計.md | 45分 |
| 14 | [業務まるごと RPA](units/14-browser-rpa/) | 繰り返しのブラウザ作業／定期実行 | rpa_flow.py、実行ログ、運用メモ | 60分 |

合計 約10.3時間。単元01→02→09 を先にやると、以降が楽になります。

### 単元13・14 には練習用のシステムが付いています

[`apps/rpa-lab/`](apps/rpa-lab/) は、**わざと自動化しにくく作った**受注管理システムです。
ログイン、4ステップのウィザード、承認フロー、非同期のレポート生成があり、
スケルトン行・デバウンス・ページ送り・セッション失効など、現場で困る要素を16個仕込んであります。
依存パッケージゼロで動き、Vercel にもそのままデプロイできます。

```bash
cd apps/rpa-lab && npm run dev     # → http://localhost:4321
```

## Cowork と Claude Code の対応

| Cowork | Claude Code |
|---|---|
| 作業フォルダを選ぶ | `cd <dir>` して `claude` を起動 |
| 権限モード | 起動時のモード / `Shift+Tab` / `/permissions` |
| ファイルをドラッグして渡す | `@path/to/file` |
| グローバル指示 | `~/.claude/CLAUDE.md` |
| プロジェクト | `<repo>/CLAUDE.md`（コミットして共有） |
| Skill | `.claude/skills/<name>/SKILL.md` |
| プラグイン | `/plugin` + `.claude/settings.json` |
| スケジュールタスク | cron / GitHub Actions から `claude -p` |
| Word / Excel / PowerPoint / PDF 連携 | `xlsx` `docx` `pptx` `pdf` スキル |
| Chrome でログイン済みのアプリを操作 | Claude in Chrome 拡張 + `claude --chrome`（対話向き） |
| ブラウザ作業を無人で回す | Playwright MCP / Playwright スクリプト（定期実行向き） |
| 会話のリセット | `/clear` |
| （相当なし） | `git status` / `git diff` — **何をされたかが全部見える** |

## はじめかた

```bash
git clone <このリポジトリ>
cd claude-code-pra

# 教材データを生成する（初回、または data/ を壊したとき）
pip install openpyxl python-docx python-pptx
python3 tools/generate_all.py

# Claude Code を起動して単元01から
claude
```

各単元の `README.md` に、**そのままコピーして使えるプロンプト**が載っています。
最初は写経で構いません。単元02以降で、自分の言葉に置き換えていきます。

## 進め方の推奨

1. **単元01** で権限モードとタスクループを体験する（ここは飛ばさない）
2. **単元02** でプロンプトの型を作る
3. **単元09** で CLAUDE.md を書く — 以降の単元でプロンプトが短くなる
4. 自分の業務に近い単元（04〜08）を選んでやる
5. **単元10・11** で繰り返す仕事を仕組みに変える
6. **単元12** で全部を使う
7. **単元13・14** で、ファイルの外（Web アプリ）にも手を伸ばす

## 全単元に共通するルール

- `units/*/data/` は読み取り専用。成果物は `units/*/output/` に書く
- ファイルを削除しない。不要なものは退避する
- 推測でデータを埋めない。不明点は「要確認」として残す
- 判断が必要なことを Claude に決めさせない。判断材料を出させて、人が決める

この4つは、Cowork でも Claude Code でも変わらない、AIに仕事を任せるときの基本です。

## ライセンスと免責

教材内の会社名・人名・数値はすべて架空のものです。
Claude Academy の公式教材ではなく、そのユースケースを Claude Code 向けに再構成した非公式教材です。
