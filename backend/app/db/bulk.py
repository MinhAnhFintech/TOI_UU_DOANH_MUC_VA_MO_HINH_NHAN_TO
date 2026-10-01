"""Ghi hàng loạt (bulk upsert) dùng chung cho các script thu thập dữ liệu.

Gửi theo lô INSERT ... ON CONFLICT DO UPDATE thay vì từng dòng một, vì mỗi lượt
gửi qua mạng tới Supabase mất vài chục mili-giây.
"""
from __future__ import annotations

import math
import time
from typing import Iterable, Sequence

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


def clean_value(value):
    """Đổi kiểu numpy/pandas sang kiểu Python; NaN/NaT/inf -> None."""
    if value is None:
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    try:  # pandas.NaT / pandas.NA
        import pandas as pd
        if value is pd.NaT or value is pd.NA:
            return None
    except Exception:
        pass
    return value


def bulk_upsert(
    session,
    engine,
    table,
    rows: Iterable[dict],
    update_cols: Sequence[str] | None = None,
    chunk_size: int = 500,
    retries: int = 2,
) -> int:
    """Upsert `rows` (list các dict) vào `table` theo lô.

    update_cols: các cột sẽ bị ghi đè khi trùng khoá chính. Mặc định: mọi cột
    không thuộc khoá chính có mặt trong dòng dữ liệu. Chỉ liệt kê vài cột nếu muốn
    giữ nguyên các cột còn lại (vd. chỉ cập nhật shares_outstanding, market_cap).
    """
    rows = [{k: clean_value(v) for k, v in row.items()} for row in rows]
    if not rows:
        return 0
    pk = [c.name for c in table.primary_key.columns]
    keys = list(rows[0].keys())
    # Mọi dòng trong một lô INSERT ... VALUES phải có cùng tập cột.
    rows = [{k: row.get(k) for k in keys} for row in rows]
    if update_cols is None:
        update_cols = [k for k in keys if k not in pk]
    insert = sqlite_insert if engine.dialect.name == "sqlite" else pg_insert

    for attempt in range(1, retries + 1):
        try:
            for i in range(0, len(rows), chunk_size):
                stmt = insert(table).values(rows[i:i + chunk_size])
                if update_cols:
                    stmt = stmt.on_conflict_do_update(
                        index_elements=pk, set_={c: stmt.excluded[c] for c in update_cols}
                    )
                else:
                    stmt = stmt.on_conflict_do_nothing(index_elements=pk)
                session.execute(stmt)
            session.commit()
            return len(rows)
        except Exception:
            session.rollback()
            if attempt == retries:
                raise
            time.sleep(2)
    return 0
