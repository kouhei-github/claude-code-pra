# -*- coding: utf-8 -*-
"""単元14の模範解答: 受注登録 → 承認 → レポート取得 を通しで自動化する。

先に自分で書いてから開くこと。

前提:
    pip install playwright && playwright install chromium
    cd apps/rpa-lab && npm run dev      # http://localhost:4321

使い方:
    RPA_LAB_URL=http://localhost:4321 \
    RPA_SALES_PASSWORD=... RPA_APPROVER_PASSWORD=... \
    python3 units/14-browser-rpa/solution/rpa_flow.py --input units/14-browser-rpa/data/受注登録キュー.csv

設計の要点:
    - 認証情報はコードに書かず環境変数から読む
    - 「待つ」は sleep ではなく expect/wait_for で条件を待つ
    - 1件の失敗で全体を止めない。結果を1行ずつ記録して最後に集計する
    - 二重登録を防ぐため、登録前に同じ顧客・同じ納期の申請中がないか確認する
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

BASE = os.environ.get("RPA_LAB_URL", "http://localhost:4321")
SALES = (
    os.environ.get("RPA_SALES_EMAIL", "tanaka@altair.example.co.jp"),
    os.environ.get("RPA_SALES_PASSWORD", ""),
)
APPROVER = (
    os.environ.get("RPA_APPROVER_EMAIL", "okochi@altair.example.co.jp"),
    os.environ.get("RPA_APPROVER_PASSWORD", ""),
)
ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = ROOT / "units/14-browser-rpa/output"


def log(*a):
    print(f"[{datetime.now():%H:%M:%S}]", *a, flush=True)


# ---------------------------------------------------------------- ログイン
def login(page: Page, email: str, password: str) -> None:
    """ログイン画面を通す。すでにセッションがあればダッシュボードに飛ぶ。"""
    if not password:
        sys.exit("パスワードが未設定です。RPA_SALES_PASSWORD / RPA_APPROVER_PASSWORD を設定してください。")
    page.goto(f"{BASE}/", wait_until="domcontentloaded")
    # 既存セッションのリダイレクトを待つ
    page.wait_for_timeout(300)
    if "/dashboard" in page.url:
        log("既存セッションを再利用")
        dismiss_notice(page)
        return

    page.fill("[data-testid=email]", email)
    page.fill("[data-testid=password]", password)
    page.click("[data-testid=login-submit]")
    try:
        page.wait_for_url("**/dashboard", timeout=15000)
    except PWTimeout:
        err = page.locator("[data-testid=login-error]")
        raise RuntimeError(f"ログインに失敗: {err.inner_text() if err.is_visible() else '原因不明'}")
    log(f"ログイン成功: {email}")
    dismiss_notice(page)


def dismiss_notice(page: Page) -> None:
    """ログイン直後に1回だけ出るお知らせモーダルを閉じる。出ないこともある。"""
    modal = page.locator("[data-testid=modal]")
    try:
        modal.wait_for(state="visible", timeout=2500)
    except PWTimeout:
        return
    modal.locator("[data-testid=modal-confirm]").click()
    modal.wait_for(state="detached", timeout=5000)
    log("お知らせモーダルを閉じた")


def ensure_logged_in(page: Page, creds) -> None:
    """セッション切れで /?expired=1 に飛ばされていたら入り直す。"""
    if "expired" in page.url or page.url.rstrip("/") == BASE.rstrip("/"):
        log("セッション切れを検知。再ログインする")
        login(page, *creds)


# ------------------------------------------------------------ 受注の登録
def wait_rows(page: Page, tbody: str, empty: str, timeout: int = 20000) -> None:
    """一覧の読み込み完了を待つ。

    ここが RPA で一番間違えやすいところ。単に "tbody tr" を待つと、
    読み込み中に描画されるスケルトン行（<tr><td class="skeleton">）を
    掴んでしまい、0 件だと誤判定する。
    「データ行が出る」か「0件表示が出る」か、どちらかを待つのが正しい。
    """
    page.wait_for_selector(
        f"[data-testid={tbody}] tr[data-order-id], [data-testid={empty}]", timeout=timeout
    )


def find_existing(page: Page, order_key: str) -> bool:
    """同じキーの受注がすでにあるなら True。二重登録の防止に使う。"""
    page.goto(f"{BASE}/orders?q={order_key}", wait_until="domcontentloaded")
    wait_rows(page, "order-rows", "no-results")
    return page.locator("[data-testid=order-rows] tr[data-order-id]").count() > 0


def create_order(page: Page, row: dict) -> str:
    """4ステップのウィザードを最後まで進めて受注番号を返す。"""
    page.goto(f"{BASE}/order-new", wait_until="domcontentloaded")
    # 「要素がある」と「使える状態になっている」は別。<select> は最初に
    # 空の状態で描画され、あとから API 経由で選択肢が入る。要素の存在だけを
    # 待つと、選択肢ゼロの状態を読んでしまう。
    page.wait_for_function(
        "document.querySelectorAll('[data-testid=customer] option').length > 1",
        timeout=20000)

    # Step 1: 顧客
    #
    # いきなり select_option すると、選択肢に無いときに 30 秒待たされたうえで
    # 「Timeout」としか分からない。先に選択肢を読んで、業務的な言葉で落とす。
    options = page.locator("[data-testid=customer] option").all_inner_texts()
    if row["顧客名"] not in options:
        raise LookupError(f"顧客マスタに存在しません: {row['顧客名']}")
    page.select_option("[data-testid=customer]", label=row["顧客名"])
    if row.get("営業担当"):
        page.fill("[data-testid=rep]", row["営業担当"])
    page.click("[data-testid=wizard-next]")

    # Step 2: 明細（1商品につきモーダルを1回開く）
    for code, qty in parse_lines(row["明細"]):
        page.click("[data-testid=add-line]")
        modal = page.locator("[data-testid=modal]")
        modal.wait_for(state="visible", timeout=5000)
        modal.locator("[data-testid=product-search]").fill(code)
        option = modal.locator(f"[data-testid=product-options] [data-code='{code}']")
        try:
            option.wait_for(state="visible", timeout=3000)
        except PWTimeout:
            modal.locator("[data-testid=modal-cancel]").click()
            raise LookupError(f"商品マスタに存在しません: {code}")
        option.click()
        modal.locator("[data-testid=qty]").fill(str(qty))
        modal.locator("[data-testid=modal-confirm]").click()
        modal.wait_for(state="detached", timeout=5000)
    page.click("[data-testid=wizard-next]")

    # Step 3: 納期・備考
    page.fill("[data-testid=due-date]", row["納期"])
    if row.get("備考"):
        page.fill("[data-testid=note]", row["備考"])
    page.click("[data-testid=wizard-next]")

    # 画面のバリデーションに引っかかると次のステップに進まない。
    # 「進めなかった」ことを検知して、画面が出しているエラー文をそのまま拾う。
    due_err = page.locator("#err-due")
    if due_err.is_visible():
        raise ValueError(f"納期が不正です（{row['納期']}）: {due_err.inner_text()}")

    # Step 4: 確認して申請
    #
    # 注意: トーストは明細追加のたびに出て 5 秒残る。単に「最初のトースト」を
    # 待つと、明細追加時のトーストを掴んでしまう。成功したら受注一覧へ
    # リダイレクトされるので、URL の遷移を成功条件にするほうが確実。
    page.wait_for_selector("[data-testid=review]", state="visible", timeout=5000)
    page.click("[data-testid=wizard-submit]")
    try:
        page.wait_for_url("**/orders?q=SO-*", timeout=25000)
    except PWTimeout:
        err = page.locator("[data-testid=toast].error").last
        detail = err.inner_text() if err.count() else "原因不明（リダイレクトされなかった）"
        raise RuntimeError(f"申請に失敗: {detail}")
    order_id = page.url.split("q=")[-1]
    log(f"登録: {order_id} / {row['顧客名']}")
    return order_id


def parse_lines(spec: str):
    """'P-002x2;P-102x10' → [('P-002', 2), ('P-102', 10)]"""
    out = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        code, _, qty = part.partition("x")
        out.append((code.strip(), int(qty)))
    if not out:
        raise ValueError(f"明細を解釈できません: {spec!r}")
    return out


# -------------------------------------------------------------- 承認する
def approve(page: Page, order_id: str) -> None:
    page.goto(f"{BASE}/approvals", wait_until="domcontentloaded")
    wait_rows(page, "approval-rows", "no-pending")

    # 一覧はページ送りされる。対象が見つかるまで次ページを辿る
    while True:
        row = page.locator(f"[data-testid=approval-rows] tr[data-order-id='{order_id}']")
        if row.count():
            break
        nxt = page.locator("[data-testid=page-next]")
        if nxt.is_disabled():
            raise RuntimeError(f"承認待ち一覧に {order_id} が見つからない")
        # 「次へ」を押したあと、表の中身が入れ替わるまで待つ。
        # ページ番号の表示が変わるのを条件にするのが確実。
        before = page.locator("[data-testid=page-indicator]").inner_text()
        nxt.click()
        page.wait_for_function(
            "before => document.querySelector('[data-testid=page-indicator]').textContent !== before",
            arg=before, timeout=20000)
        wait_rows(page, "approval-rows", "no-pending")

    row.locator(f"[data-approve='{order_id}']").click()
    modal = page.locator("[data-testid=modal]")
    modal.wait_for(state="visible", timeout=5000)
    modal.locator("[data-testid=modal-confirm]").click()
    modal.wait_for(state="detached", timeout=20000)
    log(f"承認: {order_id}")


# ---------------------------------------------------------- レポート取得
def download_report(page: Page, month: str, dest: Path) -> Path:
    page.goto(f"{BASE}/reports", wait_until="domcontentloaded")
    page.select_option("[data-testid=report-month]", month)
    page.click("[data-testid=generate-report]")

    # 生成は非同期。完了するまでダウンロード領域は出ない
    page.wait_for_selector("[data-testid=download-area]:not([hidden])", timeout=60000)
    with page.expect_download(timeout=30000) as dl:
        page.click("[data-testid=download-report]")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dl.value.save_as(dest)
    log(f"レポート取得: {dest}")
    return dest


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(ROOT / "units/14-browser-rpa/data/受注登録キュー.csv"))
    ap.add_argument("--month", default="2026-09")
    ap.add_argument("--headed", action="store_true", help="ブラウザを表示して実行する")
    args = ap.parse_args()

    rows = list(csv.DictReader(Path(args.input).read_text(encoding="utf-8").splitlines()))
    results = []

    with sync_playwright() as p:
        # 環境によっては Chromium の場所を明示する必要がある
        launch = {"headless": not args.headed}
        if os.environ.get("RPA_CHROMIUM_PATH"):
            launch["executable_path"] = os.environ["RPA_CHROMIUM_PATH"]
        browser = p.chromium.launch(**launch)

        # --- 営業アカウントで登録 ---
        sales_ctx = browser.new_context(accept_downloads=True)
        page = sales_ctx.new_page()
        login(page, *SALES)
        # セッションを保存しておくと、次回は再ログインを省ける
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        sales_ctx.storage_state(path=str(STATE_DIR / "session_sales.json"))

        for row in rows:
            key = f"{row['顧客名']}"
            try:
                ensure_logged_in(page, SALES)
                order_id = create_order(page, row)
                results.append({**row, "受注番号": order_id, "結果": "登録成功", "エラー": ""})
            except Exception as e:  # 1件失敗しても続ける
                log(f"失敗: {key} — {e}")
                results.append({**row, "受注番号": "", "結果": "登録失敗", "エラー": str(e)[:200]})
        sales_ctx.close()

        # --- 承認アカウントで承認 ---
        appr_ctx = browser.new_context(accept_downloads=True)
        page2 = appr_ctx.new_page()
        login(page2, *APPROVER)
        for r in results:
            if r["結果"] != "登録成功":
                continue
            try:
                ensure_logged_in(page2, APPROVER)
                approve(page2, r["受注番号"])
                r["結果"] = "承認済"
            except Exception as e:
                log(f"承認失敗: {r['受注番号']} — {e}")
                r["結果"] = "承認失敗"
                r["エラー"] = str(e)[:200]

        csv_path = download_report(page2, args.month, STATE_DIR / f"受注明細_{args.month}.csv")
        appr_ctx.close()
        browser.close()

    # --- 実行ログ ---
    out = STATE_DIR / "実行ログ.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    ok = sum(1 for r in results if r["結果"] == "承認済")
    ng = len(results) - ok
    (STATE_DIR / "実行サマリ.json").write_text(
        json.dumps(
            {"実行時刻": datetime.now().isoformat(timespec="seconds"),
             "件数": len(results), "承認済": ok, "失敗": ng,
             "レポート": str(csv_path.relative_to(ROOT))},
            ensure_ascii=False, indent=2),
        encoding="utf-8")
    log(f"完了: {ok} 件承認 / {ng} 件失敗 → {out}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
