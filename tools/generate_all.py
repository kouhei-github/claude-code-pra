# -*- coding: utf-8 -*-
"""全単元の教材ファイルを再生成する。

    pip install openpyxl python-docx python-pptx
    python3 tools/generate_all.py

各スクリプトは乱数シードを固定しているため、何度実行しても同じデータが出る。
演習で data/ を壊してしまったときは、これで元に戻せる。
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODULES = [
    ("gen_01_10_12", ["unit01", "unit10", "unit12"]),
    ("gen_02_09_11", ["unit02", "unit09", "unit11"]),
    ("gen_03_files", ["main"]),
    ("gen_04_sales", ["main"]),
    ("gen_05_expenses", ["main"]),
    ("gen_06_synthesis", ["main"]),
    ("gen_07_kpi", ["main"]),
    ("gen_08_bulk", ["main"]),
]


def main():
    for mod_name, funcs in MODULES:
        mod = importlib.import_module(mod_name)
        for fn in funcs:
            getattr(mod, fn)()
    root = Path(__file__).resolve().parents[1] / "units"
    n = sum(1 for p in root.rglob("*") if p.is_file())
    print(f"\n完了: units/ 配下に {n} ファイル")


if __name__ == "__main__":
    main()
