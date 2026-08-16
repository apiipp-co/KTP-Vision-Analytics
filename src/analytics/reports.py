from __future__ import annotations

import pandas as pd

from src.services.analytics import export_columns


def masked_operational_csv(documents: pd.DataFrame) -> bytes:
    return export_columns(documents).to_csv(index=False).encode("utf-8-sig")
