# -*- coding: utf-8 -*-
"""単元04の模範検証スクリプト。

自分で書いた verify.py が思いつかないときの答え合わせ用。
先に自分で書いてから開くこと。

使い方:
    python3 units/04-spreadsheet-cleanup/solution/verify.py \
        units/04-spreadsheet-cleanup/output/売上データ_2026上期_clean.xlsx
"""
import datetime as dt
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "units/04-spreadsheet-cleanup/data/売上データ_2026上期_raw.xlsx"

BRANCHES = {"東京", "大阪", "名古屋", "福岡", "札幌"}
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))


def raw_data_rows():
    """元ファイルの「表の行」数を数える（ヘッダー・空行・小計・注記を除く）。"""
    ws = load_workbook(RAW, data_only=False)["売上明細"]
    n = 0
    for row in ws.iter_rows(min_row=6, min_col=2, max_col=11):
        vals = [c.value for c in row]
        if all(v is None for v in vals):
            continue
        if vals[0] == "小計":
            continue
        if isinstance(vals[0], str) and vals[0].startswith("※"):
            continue
        n += 1
    return n


def main(path):
    wb = load_workbook(path)
    names = wb.sheetnames
    check("必要な4シートが存在する",
          all(s in names for s in ["売上明細_clean", "除外行", "変換ルール", "検算"]),
          f"実際: {names}")

    clean = wb["売上明細_clean"]
    header = [c.value for c in clean[1]]
    rows = list(clean.iter_rows(min_row=2, values_only=True))
    rows = [r for r in rows if any(v is not None for v in r)]

    excluded = wb["除外行"] if "除外行" in names else None
    ex_rows = []
    if excluded:
        ex_rows = [r for r in excluded.iter_rows(min_row=2, values_only=True)
                   if any(v is not None for v in r)]

    # 1. 行数の保存
    raw_n = raw_data_rows()
    check("元データ行数 == clean行数 + 除外行数",
          raw_n == len(rows) + len(ex_rows),
          f"元={raw_n} clean={len(rows)} 除外={len(ex_rows)}")

    idx = {name: i for i, name in enumerate(header) if name}

    def col(r, name):
        return r[idx[name]] if name in idx else None

    # 2. 日付型と範囲
    bad_dates = [r for r in rows
                 if not isinstance(col(r, "日付"), (dt.datetime, dt.date))
                 or not (dt.date(2026, 4, 1) <= (col(r, "日付").date()
                         if isinstance(col(r, "日付"), dt.datetime)
                         else col(r, "日付")) <= dt.date(2026, 9, 30))]
    check("日付がすべて日付型で2026-04-01〜2026-09-30", not bad_dates,
          f"NG {len(bad_dates)}件 例: {bad_dates[:3]}")

    # 3. 支店の正規化
    branches = {col(r, "支店") for r in rows}
    check("支店が5種類以内に正規化されている", branches <= BRANCHES,
          f"実際: {sorted(branches)}")

    # 4. 商品コードがマスタに存在する
    master = {r[0] for r in load_workbook(RAW)["商品マスタ"].iter_rows(
        min_row=2, values_only=True) if r[0]}
    codes = {col(r, "商品コード") for r in rows}
    check("商品コードがすべてマスタに存在する", codes <= master,
          f"マスタ外: {sorted(codes - master)}")

    # 5. 金額 == 数量 × 単価（補完フラグの無い行）
    mismatch = []
    for r in rows:
        q, u, a = col(r, "数量"), col(r, "単価"), col(r, "金額")
        if None in (q, u, a):
            mismatch.append(r)
        elif q * u != a:
            mismatch.append(r)
    check("金額 == 数量 × 単価（全clean行）", not mismatch,
          f"NG {len(mismatch)}件 例: {mismatch[:3]}")

    # 6. 数値型
    bad_types = [r for r in rows
                 if not all(isinstance(col(r, c), int) for c in ["数量", "単価", "金額"])]
    check("数量・単価・金額がint型", not bad_types, f"NG {len(bad_types)}件")

    # 7. 除外行に理由が入っている
    if ex_rows:
        no_reason = [r for r in ex_rows if not any(
            isinstance(v, str) and v.strip() for v in r[1:])]
        check("除外行すべてに理由がある", not no_reason, f"理由なし {len(no_reason)}件")

    width = max(len(n) for n, _, _ in results)
    ng = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name.ljust(width)}  {'' if ok else detail}")
        ng += 0 if ok else 1
    print(f"\n{len(results) - ng}/{len(results)} passed")
    return 1 if ng else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT / "units/04-spreadsheet-cleanup/output/売上データ_2026上期_clean.xlsx")
    if not target.exists():
        print(f"見つかりません: {target}\n先に単元04のクリーニングを実行してください。")
        sys.exit(2)
    sys.exit(main(target))
