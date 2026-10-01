"""Thu thập tỷ lệ sở hữu nước ngoài (cho nhân tố FOR).

Nguồn miễn phí của vnstock chỉ cho tỷ lệ sở hữu nước ngoài HIỆN TẠI (bảng giá), không có
lịch sử theo ngày. Vì vậy có hai chế độ:

  * ảnh chụp (mặc định): lấy tỷ lệ hiện tại của từng mã và dùng cho mọi ngày. FOR khi đó là
    danh mục long-short theo mức sở hữu nước ngoài hiện tại (có hạn chế look-ahead, phải nêu
    trong báo cáo);
  * CSV: nếu bạn có lịch sử thật (CafeF, Vietstock, CTCK...), nhập bằng file CSV
    date,ticker,foreign_owned_pct[,room_total_pct,room_remaining_pct,net_foreign_buy_value].
"""
from __future__ import annotations

import re
import time

import numpy as np
import pandas as pd

COLUMNS = ["date", "ticker", "foreign_owned_pct", "room_total_pct",
           "room_remaining_pct", "net_foreign_buy_value"]


def _norm(name) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(str(p) for p in col if str(p) and not str(p).startswith("Unnamed"))
                      for col in df.columns]
    return df


def extract_ownership(board: pd.DataFrame) -> pd.DataFrame:
    """Bảng giá (price_board) -> DataFrame[ticker, foreign_owned_pct] (phần trăm, 0-100)."""
    if board is None or board.empty:
        return pd.DataFrame(columns=["ticker", "foreign_owned_pct"])
    df = _flatten_columns(board)
    sym_col = next((c for c in df.columns if _norm(c) in ("symbol", "ticker", "stocksymbol", "code")), None)
    if sym_col is None:
        return pd.DataFrame(columns=["ticker", "foreign_owned_pct"])
    candidates = []
    for c in df.columns:
        n = _norm(c)
        if "foreign" in n and ("ownership" in n or "owned" in n or "percent" in n or "ratio" in n or "pct" in n):
            if "buy" in n or "sell" in n or "room" in n:
                continue
            candidates.append(c)
    if not candidates:
        return pd.DataFrame(columns=["ticker", "foreign_owned_pct"])
    values = pd.to_numeric(df[candidates[0]], errors="coerce")
    out = pd.DataFrame({"ticker": df[sym_col].astype(str).str.upper(), "foreign_owned_pct": values})
    out = out.dropna()
    if not out.empty and out["foreign_owned_pct"].max() <= 1.0:   # dạng thập phân -> phần trăm
        out["foreign_owned_pct"] = out["foreign_owned_pct"] * 100.0
    return out.drop_duplicates("ticker")


def fetch_ownership_snapshot(tickers: list[str], pause: float = 3.5, verbose: bool = True) -> pd.DataFrame:
    """Lấy tỷ lệ sở hữu nước ngoài hiện tại từ bảng giá vnstock (thử KBS rồi VCI)."""
    from vnstock.api.trading import Trading
    errors = []
    for source in ("KBS", "VCI"):
        try:
            # get_all=True: bảng giá mặc định đã lược bớt cột sở hữu nước ngoài.
            board = Trading(source=source, symbol=tickers[0]).price_board(symbols_list=tickers, get_all=True)
            result = extract_ownership(board)
            time.sleep(pause)
            if len(result) >= 6:
                if verbose:
                    print(f"   ✅ Nguồn {source}: có tỷ lệ sở hữu nước ngoài của {len(result)} mã")
                return result
            foreign_cols = [str(c) for c in getattr(board, "columns", []) if "foreign" in str(c).lower()]
            errors.append(f"{source}: không có cột sở hữu nước ngoài (các cột có chữ 'foreign': "
                          f"{', '.join(foreign_cols) or 'không có'})")
        except Exception as exc:
            errors.append(f"{source}: {exc}")
    if verbose:
        print("   ❌ " + " | ".join(errors)[:600])
    return pd.DataFrame(columns=["ticker", "foreign_owned_pct"])


def expand_snapshot(snapshot: pd.DataFrame, trading_days: pd.DataFrame) -> pd.DataFrame:
    """Gán tỷ lệ hiện tại cho mọi ngày giao dịch của từng mã (trading_days: cột date, ticker)."""
    merged = trading_days.merge(snapshot[["ticker", "foreign_owned_pct"]], on="ticker", how="inner")
    for col in COLUMNS[3:]:
        merged[col] = np.nan
    return merged[COLUMNS]


def read_foreign_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = {"date", "ticker", "foreign_owned_pct"} - set(df.columns)
    if missing:
        raise ValueError(f"File CSV thiếu cột bắt buộc: {', '.join(sorted(missing))}")
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    return df[COLUMNS]


class ForeignCollector:
    """Giữ lại giao diện cũ: collect(tickers, start, end) -> DataFrame foreign_daily."""

    def collect(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        snapshot = fetch_ownership_snapshot(tickers, verbose=False)
        if snapshot.empty:
            return pd.DataFrame(columns=COLUMNS)
        days = pd.DataFrame([(d.date(), t) for t in snapshot["ticker"]
                             for d in pd.bdate_range(start, end)], columns=["date", "ticker"])
        return expand_snapshot(snapshot, days)