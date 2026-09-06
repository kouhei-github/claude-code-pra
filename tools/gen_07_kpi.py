# -*- coding: utf-8 -*-
"""単元07: 分析用の月次KPIブック(こちらは整形済み)を生成する。"""
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

OUT = Path(__file__).resolve().parents[1] / "units/07-data-analysis-report/data"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(707)

HEAD = PatternFill("solid", fgColor="1F3864")
HEADF = Font(bold=True, color="FFFFFF")


def head(ws, cols, widths):
    ws.append(cols)
    for c in ws[1]:
        c.fill, c.font = HEAD, HEADF
        c.alignment = Alignment(horizontal="center")
    for letter, w in zip("ABCDEFGHIJKL", widths):
        ws.column_dimensions[letter].width = w


def months():
    out = []
    y, m = 2024, 10
    for _ in range(24):
        out.append(f"{y}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def main():
    wb = Workbook()

    # --- 月次KPI -------------------------------------------------------
    ws = wb.active
    ws.title = "月次KPI"
    head(ws, ["年月", "MRR(円)", "新規顧客数", "解約顧客数", "期末顧客数",
              "ARPU(円)", "新規獲得コスト計(円)", "問い合わせ件数", "初回応答時間(時間)", "NPS"],
         [12, 14, 13, 13, 13, 12, 20, 15, 18, 8])

    customers = 320
    mrr = 24_800_000
    for i, ym in enumerate(months()):
        season = 1.25 if ym.endswith(("-03", "-09")) else (0.85 if ym.endswith(("-01", "-08")) else 1.0)
        new = int(random.gauss(26, 5) * season)
        # 12ヶ月目以降、解約がじわじわ悪化する(分析で見つけてほしい山)
        churn_rate = 0.017 + (0.0016 * max(0, i - 9)) + random.uniform(-0.003, 0.003)
        churned = max(1, round(customers * churn_rate))
        customers = customers + new - churned
        arpu = int(random.gauss(79_000, 2_500) + i * 260)
        mrr = int(customers * arpu)
        cac_total = int(new * random.gauss(210_000, 25_000) * (1 + i * 0.012))
        inquiries = int(customers * random.uniform(0.55, 0.8))
        frt = round(random.gauss(6.2, 1.4) + max(0, i - 12) * 0.28, 1)
        nps = int(random.gauss(34, 6) - max(0, i - 12) * 0.9)
        ws.append([ym, mrr, new, churned, customers, arpu, cac_total, inquiries, frt, nps])

    # --- チャネル別売上 -------------------------------------------------
    ws2 = wb.create_sheet("チャネル別売上")
    head(ws2, ["年月", "チャネル", "新規顧客数", "売上(円)", "獲得コスト(円)"], [12, 16, 13, 16, 16])
    weights = {"直販": 0.42, "代理店": 0.28, "Web/セルフ": 0.20, "紹介": 0.10}
    cpa = {"直販": 380_000, "代理店": 190_000, "Web/セルフ": 95_000, "紹介": 40_000}
    for r in range(2, 26):
        ym = ws.cell(row=r, column=1).value
        new_total = ws.cell(row=r, column=3).value
        for ch, w in weights.items():
            n = max(0, round(new_total * w * random.uniform(0.8, 1.2)))
            rev = int(n * random.gauss(88_000, 12_000) * (1.4 if ch == "直販" else 1.0))
            ws2.append([ym, ch, n, rev, int(n * cpa[ch] * random.uniform(0.85, 1.15))])

    # --- 解約理由 -------------------------------------------------------
    ws3 = wb.create_sheet("解約理由")
    head(ws3, ["年月", "解約理由", "件数", "解約時MRR(円)"], [12, 26, 10, 16])
    reasons = ["価格が高い", "機能不足(連携)", "機能不足(レポート)", "社内で使われなかった",
               "競合へ移行", "事業縮小/予算削減", "サポート品質"]
    for r in range(2, 26):
        ym = ws.cell(row=r, column=1).value
        churned = ws.cell(row=r, column=4).value
        remaining = churned
        for j, reason in enumerate(reasons):
            if j == len(reasons) - 1:
                n = remaining
            else:
                base = {"価格が高い": 0.24, "機能不足(連携)": 0.20, "機能不足(レポート)": 0.14,
                        "社内で使われなかった": 0.18, "競合へ移行": 0.10,
                        "事業縮小/予算削減": 0.09, "サポート品質": 0.05}[reason]
                n = min(remaining, round(churned * base * random.uniform(0.6, 1.5)))
            remaining -= n
            if n > 0:
                ws3.append([ym, reason, n, int(n * random.gauss(78_000, 9_000))])
            if remaining <= 0:
                break

    # --- 目標値 ---------------------------------------------------------
    ws4 = wb.create_sheet("目標値")
    head(ws4, ["指標", "2026年度目標", "単位", "備考"], [24, 18, 10, 40])
    for row in [
        ["MRR", 42_000_000, "円", "2026年9月末時点"],
        ["月次解約率", 1.5, "%", "顧客数ベース。2.0%を超えたらアラート"],
        ["ARPU", 90_000, "円", "アップセル込み"],
        ["CAC回収期間", 14, "ヶ月", "18ヶ月を超えたら投資見直し"],
        ["初回応答時間", 4.0, "時間", "営業時間内の中央値"],
        ["NPS", 40, "pt", "四半期調査"],
    ]:
        ws4.append(row)

    path = OUT / "KPI_月次_2024-2026.xlsx"
    wb.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
