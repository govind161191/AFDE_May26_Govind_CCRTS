"""
Export phase — write operational data and analytics to CSV and Excel files.

All output is timestamped and written to etl/exports/ by default.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# ── Path bootstrap ────────────────────────────────────────────────────────────
_etl = str(Path(__file__).parent)
if _etl not in sys.path:
    sys.path.insert(0, _etl)

from config import EXPORT_DIR  # noqa: E402

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _strip_tz(df: pd.DataFrame) -> pd.DataFrame:
    """Remove timezone info from all datetime columns (Excel requirement)."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if hasattr(df[col].dt, "tz") and df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
        elif df[col].dtype == object:
            # Convert any stray pd.Timestamp objects to strings
            df[col] = df[col].apply(
                lambda v: v.isoformat() if isinstance(v, (pd.Timestamp, datetime)) else v
            )
    return df


# ── CSV exports ───────────────────────────────────────────────────────────────

def export_complaints_csv(
    df: pd.DataFrame,
    output_dir: Path | None = None,
) -> Path:
    """Write the complaints DataFrame to a timestamped CSV file."""
    output_dir = _ensure_dir(output_dir or EXPORT_DIR)
    out = output_dir / f"complaints_export_{_ts()}.csv"
    df.to_csv(out, index=False)
    logger.info("[EXPORT] Complaints CSV -> %s  (%d rows)", out, len(df))
    return out


def export_users_csv(
    df: pd.DataFrame,
    output_dir: Path | None = None,
) -> Path:
    """Write the users DataFrame to CSV, omitting password_hash."""
    output_dir = _ensure_dir(output_dir or EXPORT_DIR)
    safe_cols = [c for c in df.columns if c != "password_hash"]
    out = output_dir / f"users_export_{_ts()}.csv"
    df[safe_cols].to_csv(out, index=False)
    logger.info("[EXPORT] Users CSV -> %s  (%d rows)", out, len(df))
    return out


# ── Excel export ──────────────────────────────────────────────────────────────

def export_analytics_excel(
    analytics: dict,
    output_dir: Path | None = None,
) -> Path:
    """Write all analytics DataFrames to a multi-sheet Excel workbook.

    Sheets:
        Overview         — scalar KPIs
        Category Summary — per-category counts and averages
        Agent Performance — per-agent metrics
        Daily Stats      — day-by-day complaint volume
        SLA Analysis     — per-complaint SLA classification
        All Complaints   — full complaint export
    """
    output_dir = _ensure_dir(output_dir or EXPORT_DIR)
    out = output_dir / f"analytics_report_{_ts()}.xlsx"

    overview_df = _build_overview_df(analytics.get("overall", {}))

    sheet_map: dict[str, pd.DataFrame] = {
        "Overview":          overview_df,
        "Category Summary":  analytics.get("category_summary", pd.DataFrame()),
        "Agent Performance": analytics.get("agent_performance", pd.DataFrame()),
        "Daily Stats":       analytics.get("daily_stats", pd.DataFrame()),
        "SLA Analysis":      analytics.get("sla_analysis", pd.DataFrame()),
        "All Complaints":    analytics.get("all_complaints", pd.DataFrame()),
    }

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet_name, df in sheet_map.items():
            if df is not None and not df.empty:
                _strip_tz(df).to_excel(writer, sheet_name=sheet_name[:31], index=False)

    logger.info("[EXPORT] Analytics Excel -> %s", out)
    return out


# ── Convenience wrapper ───────────────────────────────────────────────────────

def export_all(
    complaints_df: pd.DataFrame,
    users_df: pd.DataFrame,
    analytics: dict,
    output_dir: Path | None = None,
) -> list[Path]:
    """Run all three export operations and return the list of written paths."""
    output_dir = _ensure_dir(output_dir or EXPORT_DIR)
    paths: list[Path] = []

    if not complaints_df.empty:
        paths.append(export_complaints_csv(complaints_df, output_dir))
    if not users_df.empty:
        paths.append(export_users_csv(users_df, output_dir))

    # Only write Excel if there is at least one non-empty analytics DataFrame
    has_data = analytics and any(
        isinstance(v, pd.DataFrame) and not v.empty
        for v in analytics.values()
    )
    if has_data:
        paths.append(export_analytics_excel(analytics, output_dir))
    else:
        logger.info("[EXPORT] Skipping Excel export — no analytics data available")

    return paths


# ── Internal ──────────────────────────────────────────────────────────────────

def _build_overview_df(overall: dict) -> pd.DataFrame:
    if not overall:
        return pd.DataFrame()
    rows = [
        {
            "Metric": key.replace("_", " ").title(),
            "Value": (
                f"{val:.2f}" if isinstance(val, float) and val is not None else str(val)
            ),
        }
        for key, val in overall.items()
    ]
    return pd.DataFrame(rows)
