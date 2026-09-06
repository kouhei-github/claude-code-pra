# -*- coding: utf-8 -*-
"""単元04: 意図的に「汚した」売上Excelを生成する。

現場でよくある崩れ方を再現している:
  - 表題・空行が先頭にあり、ヘッダーが5行目から始まる
  - 日付が5種類の書式で混在(和暦・ドット区切り・文字列・シリアル値)
  - 支店/担当者/商品コードに表記ゆれ(全半角・スペース・カナ)
  - 数値が文字列("1,200" / "10個" / 全角数字)
  - 金額が数量×単価と一致しない行、金額が空欄の行
  - 完全重複行と、表の途中に紛れ込んだ「小計」行
  - 結合セル、右端に注記列
"""
import datetime as dt
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

OUT = Path(__file__).resolve().parents[1] / "units/04-spreadsheet-cleanup/data"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(404)

BRANCHES = ["東京", "東京支店", " 東京", "東京　支店", "ﾄｳｷｮｳ",
            "大阪", "大阪支店", "ｵｵｻｶ", "大阪 ",
            "名古屋", "名古屋支店", "福岡", "福岡支店", "ﾌｸｵｶ", "札幌", "札幌支店"]

REPS = {
    "東京": ["山田 太郎", "山田太郎", "ヤマダタロウ", "佐藤 花子", "佐藤花子"],
    "大阪": ["鈴木 一郎", "鈴木一郎", "ｽｽﾞｷｲﾁﾛｳ", "高橋 みゆき", "高橋みゆき"],
    "名古屋": ["田中 健", "田中健", "伊藤 さくら"],
    "福岡": ["渡辺 剛", "渡辺剛", "ﾜﾀﾅﾍﾞﾂﾖｼ"],
    "札幌": ["中村 優", "中村優"],
}

PRODUCTS = [
    ("P-001", "スタンダードプラン(年間)", 120000),
    ("P-002", "プロプラン(年間)", 360000),
    ("P-003", "エンタープライズ(年間)", 1200000),
    ("P-101", "導入支援パッケージ", 250000),
    ("P-102", "追加ユーザーライセンス", 8000),
    ("P-103", "オンサイト研修(1日)", 180000),
    ("P-201", "APIアドオン", 45000),
    ("P-202", "SSOアドオン", 60000),
]

CODE_VARIANTS = {
    "P-001": ["P-001", "p-001", "P001", "ｐ-001"],
    "P-002": ["P-002", "P002", "p-002"],
    "P-003": ["P-003", "P003"],
    "P-101": ["P-101", "p101"],
    "P-102": ["P-102", "P102", "P-102 "],
    "P-103": ["P-103"],
    "P-201": ["P-201", "p-201"],
    "P-202": ["P-202", "P202"],
}

NAME_VARIANTS = {
    "スタンダードプラン(年間)": ["スタンダードプラン(年間)", "スタンダードプラン（年間）", "スタンダード プラン(年間)"],
    "プロプラン(年間)": ["プロプラン(年間)", "プロプラン（年間）", "Proプラン(年間)"],
    "エンタープライズ(年間)": ["エンタープライズ(年間)", "エンタープライズ（年間）"],
    "導入支援パッケージ": ["導入支援パッケージ", "導入支援ﾊﾟｯｹｰｼﾞ"],
    "追加ユーザーライセンス": ["追加ユーザーライセンス", "追加ユーザライセンス"],
    "オンサイト研修(1日)": ["オンサイト研修(1日)", "オンサイト研修（1日）"],
    "APIアドオン": ["APIアドオン", "ＡＰＩアドオン"],
    "SSOアドオン": ["SSOアドオン", "SSO アドオン"],
}

CHANNEL = ["直販", "代理店", "ﾊﾟｰﾄﾅｰ", "パートナー", "直販 ", "Web", "web"]
NOTES = ["", "", "", "", "要フォロー", "値引き交渉あり\n次回見直し", "初回契約", "更新見送りリスク", " ", "検収待ち"]

ZEN = str.maketrans("0123456789", "０１２３４５６７８９")


def fmt_date(d, style):
    if style == 0:
        return d.strftime("%Y/%m/%d")
    if style == 1:
        return f"{d.year}-{d.month}-{d.day}"
    if style == 2:
        return f"令和{d.year - 2018}年{d.month}月{d.day}日"
    if style == 3:
        return d.strftime("%d.%m.%Y")
    return dt.datetime(d.year, d.month, d.day)  # 本物の日付型


def fmt_qty(q, style):
    if style == 0:
        return q
    if style == 1:
        return f"{q}個"
    if style == 2:
        return str(q).translate(ZEN)
    return str(q)


def fmt_price(p, style):
    if style == 0:
        return p
    if style == 1:
        return f"{p:,}"
    return f"¥{p:,}"


def build_rows(n=118):
    rows = []
    start = dt.date(2026, 4, 1)
    for i in range(n):
        d = start + dt.timedelta(days=random.randint(0, 182))
        base_branch = random.choice(list(REPS.keys()))
        branch = random.choice([b for b in BRANCHES if b.strip().replace("　", " ").startswith(base_branch)]
                               or [base_branch])
        rep = random.choice(REPS[base_branch])
        code, name, unit = random.choice(PRODUCTS)
        qty = random.choice([1, 1, 1, 2, 2, 3, 5, 10, 20, 50])
        amount = qty * unit

        # 2割の行で金額を壊す(空欄 or 計算間違い)
        r = random.random()
        if r < 0.10:
            amount_cell = None
        elif r < 0.18:
            amount_cell = amount + random.choice([-10000, 1000, 5000, -500])
        else:
            amount_cell = fmt_price(amount, random.choice([0, 0, 0, 1]))

        rows.append([
            fmt_date(d, random.choice([0, 0, 0, 1, 2, 3, 4])),
            branch,
            rep,
            random.choice(CODE_VARIANTS[code]),
            random.choice(NAME_VARIANTS[name]),
            fmt_qty(qty, random.choice([0, 0, 0, 1, 2, 3])),
            fmt_price(unit, random.choice([0, 0, 1, 2])),
            amount_cell,
            random.choice(CHANNEL),
            random.choice(NOTES),
        ])

    # 完全重複を6行差し込む
    for _ in range(6):
        rows.insert(random.randint(0, len(rows) - 1), list(random.choice(rows)))
    return rows


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "売上明細"

    header_fill = PatternFill("solid", fgColor="D9E1F2")
    ws["B2"] = "2026年度 上期 売上明細（社内限）"
    ws["B2"].font = Font(size=14, bold=True)
    ws.merge_cells("B2:F2")
    ws["B3"] = "作成: 営業企画部 / 最終更新 2026-10-02 ※各支店から集めたものを貼り付けただけです"
    ws["B3"].font = Font(size=9, color="808080")
    ws.merge_cells("B3:H3")

    headers = ["日付", "支店", "担当者", "商品コード", "商品名", "数量", "単価", "金額", "販路", "備考"]
    for j, h in enumerate(headers, start=2):
        c = ws.cell(row=5, column=j, value=h)
        c.font = Font(bold=True)
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center")

    rows = build_rows()
    r = 6
    inserted_subtotal = 0
    for idx, row in enumerate(rows):
        # 空行をランダムに挟む
        if idx and idx % 37 == 0:
            r += 1
        # 表の途中に「小計」行を紛れ込ませる
        if idx and idx % 51 == 0 and inserted_subtotal < 2:
            ws.cell(row=r, column=2, value="小計")
            ws.cell(row=r, column=8, value="=SUM(I6:I{})".format(r - 1))
            inserted_subtotal += 1
            r += 1
        for j, v in enumerate(row, start=2):
            ws.cell(row=r, column=j, value=v)
        r += 1

    ws.cell(row=r + 2, column=2, value="※金額が空欄の行は請求書発行待ちです（担当: 佐藤）")
    ws.column_dimensions["B"].width = 16
    for col in "CDEF":
        ws.column_dimensions[col].width = 18
    ws.column_dimensions["F"].width = 26
    ws.column_dimensions["K"].width = 24

    # 商品マスタ(こちらは比較的きれい)
    ws2 = wb.create_sheet("商品マスタ")
    ws2.append(["商品コード", "商品名", "定価", "カテゴリ"])
    for c in ws2[1]:
        c.font = Font(bold=True)
        c.fill = header_fill
    cat = {"P-001": "サブスク", "P-002": "サブスク", "P-003": "サブスク",
           "P-101": "プロフェッショナルサービス", "P-102": "サブスク",
           "P-103": "プロフェッショナルサービス", "P-201": "アドオン", "P-202": "アドオン"}
    for code, name, unit in PRODUCTS:
        ws2.append([code, name, unit, cat[code]])
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 28
    ws2.column_dimensions["D"].width = 12
    ws2.column_dimensions["E"].width = 26

    ws3 = wb.create_sheet("メモ")
    for i, line in enumerate([
        "・4/15の名古屋分は担当者不在のため後日追記予定",
        "・代理店経由は「ﾊﾟｰﾄﾅｰ」表記が混ざっています",
        "・単価はマスタ準拠。値引きした場合は備考に書いてあるはず",
        "・重複していそうな行があるとの指摘あり（未確認）",
    ], start=1):
        ws3.cell(row=i, column=1, value=line)
    ws3.column_dimensions["A"].width = 70

    path = OUT / "売上データ_2026上期_raw.xlsx"
    wb.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
