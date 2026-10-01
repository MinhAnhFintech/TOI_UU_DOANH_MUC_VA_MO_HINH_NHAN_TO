"""Thu thập dữ liệu cơ bản theo quý (vốn chủ sở hữu, tổng tài sản, lợi nhuận, ROE,
số cổ phiếu lưu hành) cho Book/Market (HML), ROE (RMW), tăng trưởng tài sản (CMA)
và vốn hóa (SMB, trọng số danh mục).

Chia làm hai phần:
  * các hàm thuần (parse_*, estimate_report_date, normalize_units, ...): không gọi mạng,
    có thể kiểm thử bằng dữ liệu giả;
  * FundamentalsCollector: gọi vnstock (VCI) để lấy dữ liệu thật.

vnstock chỉ trả mặc định 4 kỳ gần nhất. Collector gọi hàm nội bộ của nhà cung cấp VCI
với limit lớn để lấy ~6 năm lịch sử; nếu không lấy được thì in rõ lý do và script
collect_fundamentals.py cho phép nhập từ file CSV thay thế.
"""
from __future__ import annotations

import re
import time
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

FIELDS = ["book_equity", "total_assets", "net_income", "roe", "shares_outstanding", "bvps"]

# Tên cột (đã chuẩn hoá: chữ thường, bỏ ký tự không phải chữ/số) -> trường chuẩn.
_ALIASES = {
    "book_equity": ["equity", "ownersequity", "bookequity", "totalequity", "vonchusohuu"],
    "total_assets": ["totalassets", "tongtaisan", "tongcongtaisan"],
    "net_income": ["netincome", "profitaftertax", "netprofit", "postaxprofit", "loinhuansauthue",
                   "profitaftertaxattributabletoparent"],
    "roe": ["roe"],
    "shares_outstanding": ["numberofsharesmktcap", "outstandingshares", "sharesoutstanding",
                           "shareoutstanding", "soluongcophieuluuhanh"],
    "bvps": ["bookvaluepershare", "bvps"],
    "equity_to_assets": ["totalequitytotalasset", "equitytoassets"],
    "market_cap": ["marketcap", "marketcapital"],
}

_YEAR_KEYS = ["year", "yearreport", "fiscalyear"]
_QUARTER_KEYS = ["quarter", "lengthreport", "quarterreport", "fiscalquarter"]
_PERIOD_RE = re.compile(r"^\s*(\d{4})\s*[-_/ ]?\s*Q\s*([1-4])\s*$", re.IGNORECASE)


def _norm(name) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _to_float(value) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return np.nan
    return v if np.isfinite(v) else np.nan


# --------------------------------------------------------------------------- #
# Chuẩn hoá khung dữ liệu trả về từ vnstock
# --------------------------------------------------------------------------- #
def _periods_as_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Đưa mọi dạng khung dữ liệu về: mỗi dòng = một quý, cột = tên chỉ tiêu (đã chuẩn hoá)."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    cols_norm = {c: _norm(c) for c in df.columns}

    # Dạng 1: mỗi dòng là một chỉ tiêu, cột là các kỳ ("2024-Q1", ...).
    period_cols = [c for c in df.columns if _PERIOD_RE.match(str(c))]
    if period_cols:
        id_col = next((c for c in ("item_id", "item_en", "item") if c in df.columns), None)
        if id_col is None:
            return pd.DataFrame()
        # Dùng cả item_id lẫn item_en/item làm tên chỉ tiêu: mỗi chỉ tiêu có thể khớp qua tên nào cũng được.
        frames = {}
        for name_col in [c for c in ("item_id", "item_en", "item") if c in df.columns]:
            for _, row in df.iterrows():
                key = _norm(row[name_col])
                if key and key not in frames:
                    frames[key] = row[period_cols]
        wide = pd.DataFrame(frames)  # index = kỳ, cột = chỉ tiêu
        wide.index = [str(i) for i in wide.index]
        out = wide.apply(pd.to_numeric, errors="coerce")
        years, quarters = [], []
        for label in out.index:
            m = _PERIOD_RE.match(label)
            years.append(int(m.group(1)))
            quarters.append(int(m.group(2)))
        out.insert(0, "quarter", quarters)
        out.insert(0, "fiscal_year", years)
        return out.reset_index(drop=True)

    # Dạng 2: mỗi dòng là một kỳ (dữ liệu thô), có cột năm và quý.
    ycol = next((c for c, n in cols_norm.items() if n in _YEAR_KEYS), None)
    qcol = next((c for c, n in cols_norm.items() if n in _QUARTER_KEYS), None)
    if ycol is None or qcol is None:
        return pd.DataFrame()
    out = pd.DataFrame({
        "fiscal_year": pd.to_numeric(df[ycol], errors="coerce"),
        "quarter": pd.to_numeric(df[qcol], errors="coerce"),
    })
    for c in df.columns:
        if c in (ycol, qcol):
            continue
        key = cols_norm[c]
        if key not in out.columns:
            out[key] = pd.to_numeric(df[c], errors="coerce")
    out = out.dropna(subset=["fiscal_year", "quarter"])
    out = out[(out["quarter"] >= 1) & (out["quarter"] <= 4)]
    out[["fiscal_year", "quarter"]] = out[["fiscal_year", "quarter"]].astype(int)
    return out.reset_index(drop=True)


def _pick(rows: pd.DataFrame, field: str) -> pd.Series:
    for alias in _ALIASES[field]:
        if alias in rows.columns and rows[alias].notna().any():
            return rows[alias]
    return pd.Series(np.nan, index=rows.index)


def parse_ratio_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Khung 'ratio' của vnstock -> bảng theo quý với các trường chuẩn.

    Trả về cột: fiscal_year, quarter, book_equity, total_assets, net_income, roe,
    shares_outstanding, bvps (thiếu thì NaN).
    """
    rows = _periods_as_rows(df)
    if rows.empty:
        return pd.DataFrame(columns=["fiscal_year", "quarter"] + FIELDS)
    out = rows[["fiscal_year", "quarter"]].copy()
    for field in FIELDS:
        out[field] = _pick(rows, field)
    # Tổng tài sản = vốn chủ / (vốn chủ / tổng tài sản) nếu nguồn chỉ có tỷ lệ.
    if out["total_assets"].isna().all():
        ratio = _pick(rows, "equity_to_assets")
        if ratio.notna().any():
            # Tỷ lệ có thể là phần trăm (vd. 9.5) hoặc số thập phân (vd. 0.095).
            r = ratio.where(ratio <= 1.5, ratio / 100.0)
            out["total_assets"] = out["book_equity"] / r.replace(0, np.nan)
    return out


def _find_item(df: pd.DataFrame, include: list[str], exclude: list[str] | None = None) -> Optional[pd.Series]:
    """Tìm dòng chỉ tiêu trong báo cáo (item rows x period columns) theo từ khoá tên."""
    period_cols = [c for c in df.columns if _PERIOD_RE.match(str(c))]
    if not period_cols:
        return None
    name_cols = [c for c in ("item_en", "item", "item_id") if c in df.columns]
    exclude = exclude or []
    for _, row in df.iterrows():
        text = " ".join(str(row[c]).lower() for c in name_cols)
        if all(k in text for k in include) and not any(k in text for k in exclude):
            values = pd.to_numeric(row[period_cols], errors="coerce")
            if values.notna().any():
                values.index = [str(i) for i in values.index]
                return values
    return None


def parse_statement_frames(balance: Optional[pd.DataFrame], income: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Bổ sung vốn chủ sở hữu, tổng tài sản (bảng cân đối) và lợi nhuận sau thuế (kết quả kinh doanh)."""
    data: dict[str, pd.Series] = {}

    def first_found(frame, *specs):
        """Thử lần lượt các bộ từ khoá, trả về chuỗi đầu tiên tìm thấy (không dùng `or` với Series)."""
        for include, exclude in specs:
            found = _find_item(frame, include, exclude)
            if found is not None:
                return found
        return None

    if balance is not None and not balance.empty:
        eq = first_found(balance,
                         (["owner", "equity"], ["contribut", "capital", "liabilit", "other"]),
                         (["total", "equity"], ["liabilit"]),
                         (["vốn chủ sở hữu"], ["nợ"]))
        ta = first_found(balance,
                         (["total assets"], ["liabilit"]),
                         (["tổng cộng tài sản"], None),
                         (["tổng tài sản"], None))
        if eq is not None:
            data["book_equity"] = eq
        if ta is not None:
            data["total_assets"] = ta
    if income is not None and not income.empty:
        ni = first_found(income,
                         (["attributable", "parent"], None),
                         (["profit after tax"], None),
                         (["net profit"], None),
                         (["lợi nhuận sau thuế"], None))
        if ni is not None:
            data["net_income"] = ni
    if not data:
        return pd.DataFrame(columns=["fiscal_year", "quarter", "book_equity", "total_assets", "net_income"])
    wide = pd.DataFrame(data)
    years, quarters = [], []
    for label in wide.index:
        m = _PERIOD_RE.match(str(label))
        years.append(int(m.group(1)) if m else np.nan)
        quarters.append(int(m.group(2)) if m else np.nan)
    wide.insert(0, "quarter", quarters)
    wide.insert(0, "fiscal_year", years)
    return wide.dropna(subset=["fiscal_year"]).astype({"fiscal_year": int, "quarter": int}).reset_index(drop=True)


def combine_sources(ratio_df: pd.DataFrame, statements_df: pd.DataFrame) -> pd.DataFrame:
    """Ghép bảng ratio và bảng báo cáo; ưu tiên số liệu báo cáo, ratio điền chỗ thiếu."""
    empty = pd.DataFrame(columns=["fiscal_year", "quarter"] + FIELDS)
    if (ratio_df is None or ratio_df.empty) and (statements_df is None or statements_df.empty):
        return empty
    if ratio_df is None or ratio_df.empty:
        merged = statements_df.copy()
    elif statements_df is None or statements_df.empty:
        merged = ratio_df.copy()
    else:
        merged = ratio_df.merge(statements_df, on=["fiscal_year", "quarter"], how="outer", suffixes=("_r", "_s"))
        for field in ("book_equity", "total_assets", "net_income"):
            s, r = merged.get(f"{field}_s"), merged.get(f"{field}_r")
            merged[field] = s.where(s.notna(), r) if s is not None and r is not None else (s if s is not None else r)
            merged = merged.drop(columns=[c for c in (f"{field}_s", f"{field}_r") if c in merged])
    for field in FIELDS:
        if field not in merged:
            merged[field] = np.nan
    merged = merged.drop_duplicates(["fiscal_year", "quarter"], keep="first")
    return merged.sort_values(["fiscal_year", "quarter"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Ngày công bố báo cáo, đơn vị, vốn hóa
# --------------------------------------------------------------------------- #
def estimate_report_date(fiscal_year: int, quarter: int) -> date:
    """vnstock không có ngày công bố thật -> ước lượng thận trọng theo hạn pháp lý.

    Quý 1-3: 45 ngày sau khi kết thúc quý; quý 4 (báo cáo năm đã kiểm toán): 90 ngày.
    Bộ dựng nhân tố còn cộng thêm 1 tháng nữa nên không dùng số liệu trước khi công bố.
    """
    quarter_end = pd.Timestamp(year=int(fiscal_year), month=int(quarter) * 3, day=1) + pd.offsets.MonthEnd(0)
    return (quarter_end + pd.Timedelta(days=90 if int(quarter) == 4 else 45)).date()


def normalize_units(df: pd.DataFrame, last_close_vnd: float | None = None) -> tuple[pd.DataFrame, float]:
    """Đưa vốn chủ/tài sản/lợi nhuận về cùng đơn vị VND với vốn hoá (giá VND x số cổ phiếu).

    Nếu Book/Market trung vị nằm ngoài khoảng hợp lý (0.005 - 200) thì thử các hệ số
    1e3, 1e6, 1e9 (và nghịch đảo) để đưa về 0.05 - 50. Trả về (khung dữ liệu, hệ số đã nhân). Hệ số 1.0 nghĩa là không đổi.
    """
    df = df.copy()
    if df.empty or last_close_vnd is None:
        return df, 1.0
    last = df.dropna(subset=["book_equity", "shares_outstanding"]).tail(4)
    if last.empty:
        return df, 1.0
    market_cap = float(last_close_vnd) * last["shares_outstanding"]
    bm = (last["book_equity"] / market_cap).median()
    if not np.isfinite(bm) or bm <= 0:
        return df, 1.0
    if 0.005 <= bm <= 200:      # đã hợp lý (Book/Market thực tế của VN30 khoảng 0.1 - 5)
        return df, 1.0
    for factor in (1e3, 1e6, 1e9, 1e-3, 1e-6, 1e-9):
        if 0.05 <= bm * factor <= 50:
            for col in ("book_equity", "total_assets", "net_income"):
                df[col] = df[col] * factor
            return df, factor
    return df, 1.0


def finalize_quarterly(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Thêm ticker, report_date; chuẩn hoá ROE về dạng thập phân."""
    out = df.copy()
    out["ticker"] = ticker
    out["report_date"] = [estimate_report_date(y, q) for y, q in zip(out["fiscal_year"], out["quarter"])]
    roe = pd.to_numeric(out["roe"], errors="coerce")
    if roe.notna().any() and roe.abs().median() > 1.5:   # đang ở dạng phần trăm
        roe = roe / 100.0
    out["roe"] = roe
    return out


# --------------------------------------------------------------------------- #
# Gọi vnstock
# --------------------------------------------------------------------------- #
class FundamentalsCollector:
    """Lấy dữ liệu quý từ vnstock. Mỗi lần gọi mạng nghỉ `pause` giây để không bị giới hạn tốc độ."""

    def __init__(self, limit: int = 40, pause: float = 3.5, verbose: bool = True):
        self.limit = limit
        self.pause = pause
        self.verbose = verbose

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)

    # -- VCI, gọi hàm nội bộ để vượt giới hạn mặc định 4 kỳ --
    def _vci_provider(self, ticker: str):
        from vnstock.explorer.vci.financial import Finance as VciFinance
        return VciFinance(symbol=ticker, period="quarter", get_all=True, show_log=False)

    def _vci_report(self, provider, report_type: str, mode: str) -> pd.DataFrame:
        kwargs = dict(report_type=report_type, lang="en", mode=mode, get_all=True,
                      period="quarter", limit=self.limit)
        try:
            return provider._get_report(**kwargs)
        finally:
            time.sleep(self.pause)

    def fetch_ticker(self, ticker: str) -> pd.DataFrame:
        """Trả về bảng theo quý (chưa có report_date). Rỗng nếu không lấy được."""
        ratio_df = pd.DataFrame()
        statements = pd.DataFrame()
        errors = []
        try:
            provider = self._vci_provider(ticker)
            try:
                ratio_df = parse_ratio_frame(self._vci_report(provider, "ratio", "raw"))
                if ratio_df.empty:   # dạng 'final' (chỉ tiêu theo dòng)
                    ratio_df = parse_ratio_frame(self._vci_report(provider, "ratio", "final"))
            except Exception as exc:
                errors.append(f"ratio: {exc}")
            try:
                balance = self._vci_report(provider, "balance_sheet", "final")
                income = self._vci_report(provider, "income_statement", "final")
                statements = parse_statement_frames(balance, income)
            except Exception as exc:
                errors.append(f"statements: {exc}")
        except Exception as exc:
            errors.append(f"VCI: {exc}")

        merged = combine_sources(ratio_df, statements)
        if merged.empty or merged["book_equity"].notna().sum() == 0:
            # Phương án cuối: API công khai (chỉ ~4 quý gần nhất).
            try:
                from vnstock.api.financial import Finance
                pub = Finance(source="VCI", symbol=ticker, period="quarter")
                fallback = parse_ratio_frame(pub.ratio(period="quarter"))
                time.sleep(self.pause)
                merged = combine_sources(fallback, pd.DataFrame())
                if not merged.empty:
                    self._log(f"   ⚠️ {ticker}: chỉ lấy được {len(merged)} quý qua API công khai")
            except Exception as exc:
                errors.append(f"public API: {exc}")
        if merged.empty and errors:
            self._log(f"   ❌ {ticker}: " + " | ".join(errors)[:300])
        return merged

    def collect(self, tickers: list[str]) -> dict[str, pd.DataFrame]:
        result = {}
        for i, ticker in enumerate(tickers, 1):
            self._log(f" 📥 [{i}/{len(tickers)}] Đang tải báo cáo tài chính {ticker}...")
            df = self.fetch_ticker(ticker)
            if not df.empty:
                result[ticker] = df
                first = f"{int(df['fiscal_year'].iloc[0])}Q{int(df['quarter'].iloc[0])}"
                last = f"{int(df['fiscal_year'].iloc[-1])}Q{int(df['quarter'].iloc[-1])}"
                self._log(f"   ✅ {ticker}: {len(df)} quý ({first} → {last}), "
                          f"có vốn chủ: {int(df['book_equity'].notna().sum())}, "
                          f"có ROE: {int(df['roe'].notna().sum())}, "
                          f"có số cổ phiếu: {int(df['shares_outstanding'].notna().sum())}")
        return result
