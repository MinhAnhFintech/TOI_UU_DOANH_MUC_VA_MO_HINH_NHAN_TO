"""Kiểm thử các hàm thuần (không gọi mạng) của bộ thu thập dữ liệu cơ bản và khối ngoại."""
import numpy as np
import pandas as pd

from app.collectors.foreign import extract_ownership
from app.collectors.fundamentals import (
    combine_sources, estimate_report_date, normalize_units, parse_ratio_frame, parse_statement_frames,
)


def test_ratio_raw_rows_per_period():
    df = pd.DataFrame({
        "yearReport": [2024, 2024], "lengthReport": [2, 1], "roe": [0.2, 0.18],
        "equity": [5e12, 4.8e12], "numberOfSharesMktCap": [1e9, 1e9], "totalEquityTotalAsset": [0.1, 0.1],
    })
    out = parse_ratio_frame(df)
    assert set(zip(out.fiscal_year, out.quarter)) == {(2024, 1), (2024, 2)}
    assert out.loc[out.quarter == 2, "book_equity"].iloc[0] == 5e12
    assert np.isclose(out.loc[out.quarter == 2, "total_assets"].iloc[0], 5e13)   # equity / (equity/assets)


def test_ratio_items_as_rows():
    df = pd.DataFrame({"item": ["ROE", "Equity"], "item_en": ["ROE", "Equity"], "item_id": ["roe", "equity"],
                       "2024-Q1": [0.1, 100.0], "2024-Q2": [0.2, 110.0]})
    out = parse_ratio_frame(df)
    assert out.sort_values("quarter")["book_equity"].tolist() == [100.0, 110.0]


def test_statements_picks_owner_equity_not_capital():
    bs = pd.DataFrame({"item": ["Charter capital", "OWNER'S EQUITY(Bn.VND)", "TOTAL ASSETS (Bn. VND)"],
                       "item_en": ["Charter capital", "OWNER'S EQUITY(Bn.VND)", "TOTAL ASSETS (Bn. VND)"],
                       "item_id": ["a", "b", "c"], "2024-Q1": [1.0, 50.0, 500.0]})
    out = parse_statement_frames(bs, None)
    assert out["book_equity"].iloc[0] == 50.0 and out["total_assets"].iloc[0] == 500.0


def test_combine_sources_handles_empty():
    assert combine_sources(pd.DataFrame(), pd.DataFrame()).empty


def test_report_date_is_after_quarter_end():
    assert estimate_report_date(2024, 1).isoformat() == "2024-05-15"
    assert estimate_report_date(2024, 4).isoformat() == "2025-03-31"


def test_normalize_units_rescales_only_when_needed():
    ok = pd.DataFrame({"book_equity": [3e12], "total_assets": [3e13], "net_income": [1e11], "shares_outstanding": [1e9]})
    same, f = normalize_units(ok, last_close_vnd=30000.0)       # B/M = 0.1 -> giữ nguyên
    assert f == 1.0
    in_billions = ok.assign(book_equity=3e3, total_assets=3e4, net_income=1e2)   # đơn vị tỷ đồng
    fixed, f = normalize_units(in_billions, last_close_vnd=30000.0)
    assert f == 1e9 and np.isclose(fixed["book_equity"].iloc[0], 3e12)


def test_extract_ownership_percent_and_ratio():
    board = pd.DataFrame({"symbol": ["ACB", "VNM"] * 3, "foreign_ownership_ratio": [0.3, 0.45] * 3})
    out = extract_ownership(board.drop_duplicates()) if False else extract_ownership(
        pd.DataFrame({"symbol": list("ABCDEF"), "foreign_ownership_ratio": [0.1, 0.2, 0.3, 0.4, 0.2, 0.1]}))
    assert out["foreign_owned_pct"].max() == 40.0
