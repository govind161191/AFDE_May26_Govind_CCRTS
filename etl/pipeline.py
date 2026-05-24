"""
CCRTS ETL Pipeline — standalone orchestrator with CLI.

Usage
-----
Run the full pipeline using sample data:
    python etl/pipeline.py --all

Import complaints from a CSV:
    python etl/pipeline.py --import-complaints etl/sample_data/complaints_import.csv

Import new users from a CSV:
    python etl/pipeline.py --import-users etl/sample_data/users_import.csv

Compute analytics and refresh summary tables:
    python etl/pipeline.py --analytics

Export data to etl/exports/:
    python etl/pipeline.py --export

Combine flags freely:
    python etl/pipeline.py --import-complaints data.csv --analytics --export

Environment variables
---------------------
  DATABASE_URL   — override the default SQLite path
  CCRTS_DB_PATH  — override just the SQLite file location
  ETL_LOG_LEVEL  — set log verbosity (default: INFO)
"""

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

# ── Path bootstrap (must come before any local imports) ───────────────────────
_backend = str(Path(__file__).parent.parent / "backend")
_etl = str(Path(__file__).parent)
for _p in (_backend, _etl):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine          # noqa: E402
from sqlalchemy.orm import sessionmaker        # noqa: E402

from config import DATABASE_URL, EXPORT_DIR, LOG_LEVEL, SAMPLE_DIR  # noqa: E402
from etl_models import ETLBase                                        # noqa: E402
from extract import (                                                 # noqa: E402
    extract_complaints_from_db,
    extract_csv,
    extract_users_from_db,
)
from transform import compute_analytics                               # noqa: E402
from transform import transform_imported_complaints                   # noqa: E402
from transform import transform_imported_users                        # noqa: E402
from load import load_complaints, load_users, log_etl_run             # noqa: E402
from load import upsert_summary_tables                                # noqa: E402
from export import export_all, export_analytics_excel                 # noqa: E402
from export import export_complaints_csv, export_users_csv            # noqa: E402


# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)-20s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ccrts.etl.pipeline")


# ── Session factory ───────────────────────────────────────────────────────────

def _make_session():
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Create both operational tables (roles, users, complaints, …) and ETL summary tables
    import models as _models  # backend models — Base declared there
    from database import Base as OperationalBase  # noqa: F401
    OperationalBase.metadata.create_all(bind=engine)
    ETLBase.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


# ── Phase: import complaints ──────────────────────────────────────────────────

def run_import_complaints(session, csv_path: str) -> dict:
    run_id = str(uuid.uuid4())
    started = datetime.utcnow()
    _banner("Import Complaints", csv_path)
    errors: list[str] = []
    try:
        raw_df = extract_csv(csv_path)
        extracted = len(raw_df)

        clean_df, transform_errors = transform_imported_complaints(raw_df, session)
        errors.extend(transform_errors)

        loaded = load_complaints(session, clean_df)
        duration = (datetime.utcnow() - started).total_seconds()

        _phase_summary("Import Complaints", extracted, len(clean_df), loaded, errors)
        log_etl_run(session, _run_record(
            run_id, "import_complaints", started, duration,
            extracted, len(clean_df), loaded, errors,
        ))
        return {"status": "success", "loaded": loaded, "errors": errors}

    except Exception as exc:
        duration = (datetime.utcnow() - started).total_seconds()
        logger.error("[PIPELINE] Import Complaints failed: %s", exc, exc_info=True)
        session.rollback()
        log_etl_run(session, _run_record(
            run_id, "import_complaints", started, duration,
            0, 0, 0, [str(exc)], status="failed",
        ))
        return {"status": "failed", "error": str(exc)}


# ── Phase: import users ───────────────────────────────────────────────────────

def run_import_users(session, csv_path: str) -> dict:
    run_id = str(uuid.uuid4())
    started = datetime.utcnow()
    _banner("Import Users", csv_path)
    errors: list[str] = []
    try:
        raw_df = extract_csv(csv_path)
        extracted = len(raw_df)

        clean_df, transform_errors = transform_imported_users(raw_df, session)
        errors.extend(transform_errors)

        loaded = load_users(session, clean_df)
        duration = (datetime.utcnow() - started).total_seconds()

        _phase_summary("Import Users", extracted, len(clean_df), loaded, errors)
        log_etl_run(session, _run_record(
            run_id, "import_users", started, duration,
            extracted, len(clean_df), loaded, errors,
        ))
        return {"status": "success", "loaded": loaded, "errors": errors}

    except Exception as exc:
        duration = (datetime.utcnow() - started).total_seconds()
        logger.error("[PIPELINE] Import Users failed: %s", exc, exc_info=True)
        log_etl_run(session, _run_record(
            run_id, "import_users", started, duration,
            0, 0, 0, [str(exc)], status="failed",
        ))
        return {"status": "failed", "error": str(exc)}


# ── Phase: analytics ──────────────────────────────────────────────────────────

def run_analytics(session) -> dict:
    run_id = str(uuid.uuid4())
    started = datetime.utcnow()
    _banner("Analytics ETL")
    try:
        analytics = compute_analytics(session)
        overall = analytics.get("overall", {})

        loaded = upsert_summary_tables(session, analytics)
        duration = (datetime.utcnow() - started).total_seconds()

        logger.info("[PIPELINE] --- Overall KPIs ---")
        for key, val in overall.items():
            display = f"{val:.2f}" if isinstance(val, float) and val is not None else str(val)
            logger.info("[PIPELINE]   %-30s %s", key, display)

        log_etl_run(session, _run_record(
            run_id, "analytics", started, duration,
            overall.get("total_complaints", 0),
            overall.get("total_complaints", 0),
            loaded, [],
        ))
        return {"status": "success", "analytics": analytics}

    except Exception as exc:
        duration = (datetime.utcnow() - started).total_seconds()
        logger.error("[PIPELINE] Analytics ETL failed: %s", exc, exc_info=True)
        log_etl_run(session, _run_record(
            run_id, "analytics", started, duration,
            0, 0, 0, [str(exc)], status="failed",
        ))
        return {"status": "failed", "error": str(exc)}


# ── Phase: export ─────────────────────────────────────────────────────────────

def run_export(session, analytics: dict | None = None, output_dir: Path | None = None) -> dict:
    run_id = str(uuid.uuid4())
    started = datetime.utcnow()
    output_dir = output_dir or EXPORT_DIR
    _banner("Export", str(output_dir))
    try:
        if analytics is None:
            analytics = compute_analytics(session)

        complaints_df = extract_complaints_from_db(session)
        users_df = extract_users_from_db(session)

        written = export_all(complaints_df, users_df, analytics, output_dir)
        duration = (datetime.utcnow() - started).total_seconds()

        logger.info("[PIPELINE] Export complete — %d files written:", len(written))
        for f in written:
            logger.info("[PIPELINE]   %s", f)

        log_etl_run(session, _run_record(
            run_id, "export", started, duration,
            len(complaints_df), 0, len(written), [],
        ))
        return {"status": "success", "files": [str(f) for f in written]}

    except Exception as exc:
        duration = (datetime.utcnow() - started).total_seconds()
        logger.error("[PIPELINE] Export failed: %s", exc, exc_info=True)
        log_etl_run(session, _run_record(
            run_id, "export", started, duration,
            0, 0, 0, [str(exc)], status="failed",
        ))
        return {"status": "failed", "error": str(exc)}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python etl/pipeline.py",
        description="CCRTS ETL Pipeline — Extract, Transform, Load & Export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  Full pipeline with bundled sample data:
    python etl/pipeline.py --all

  Import complaints then refresh analytics and export:
    python etl/pipeline.py --import-complaints etl/sample_data/complaints_import.csv
        --analytics --export

  Just refresh the ETL summary tables:
    python etl/pipeline.py --analytics

  Export current data to etl/exports/:
    python etl/pipeline.py --export
""",
    )

    parser.add_argument(
        "--import-complaints", metavar="CSV",
        help="Path to a complaints CSV file to import into the database",
    )
    parser.add_argument(
        "--import-users", metavar="CSV",
        help="Path to a users CSV file to import into the database",
    )
    parser.add_argument(
        "--analytics", action="store_true",
        help="Compute analytics and refresh ETL summary tables",
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export all data to CSV + Excel in etl/exports/",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run the full pipeline: import sample data -> analytics -> export",
    )
    parser.add_argument(
        "--output-dir", metavar="DIR",
        help=f"Directory for exported files (default: {EXPORT_DIR})",
    )

    args = parser.parse_args()

    if not any([args.import_complaints, args.import_users, args.analytics, args.export, args.all]):
        parser.print_help()
        sys.exit(0)

    session = _make_session()
    output_dir = Path(args.output_dir) if args.output_dir else EXPORT_DIR
    wall_start = time.time()

    try:
        analytics: dict | None = None

        if args.all:
            logger.info("=" * 62)
            logger.info("  CCRTS ETL PIPELINE -- Full Run")
            logger.info("=" * 62)
            run_import_users(session, str(SAMPLE_DIR / "users_import.csv"))
            run_import_complaints(session, str(SAMPLE_DIR / "complaints_import.csv"))
            result = run_analytics(session)
            analytics = result.get("analytics")
            run_export(session, analytics=analytics, output_dir=output_dir)
        else:
            if args.import_users:
                run_import_users(session, args.import_users)
            if args.import_complaints:
                run_import_complaints(session, args.import_complaints)
            if args.analytics:
                result = run_analytics(session)
                analytics = result.get("analytics")
            if args.export:
                run_export(session, analytics=analytics, output_dir=output_dir)

    finally:
        session.close()

    elapsed = time.time() - wall_start
    logger.info("-" * 60)
    logger.info("Pipeline finished in %.2fs", elapsed)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _banner(phase: str, detail: str = "") -> None:
    line = f"PHASE: {phase}" + (f"  [{detail}]" if detail else "")
    logger.info("=" * 60)
    logger.info(line)
    logger.info("=" * 60)


def _phase_summary(
    phase: str,
    extracted: int,
    transformed: int,
    loaded: int,
    errors: list[str],
) -> None:
    logger.info("--- %s summary ---", phase)
    logger.info("   Extracted:   %d", extracted)
    logger.info("   Transformed: %d", transformed)
    logger.info("   Loaded:      %d", loaded)
    if errors:
        logger.info("   Warnings/errors (%d):", len(errors))
        for msg in errors:
            logger.warning("     %s", msg)


def _run_record(
    run_id: str,
    phase: str,
    started: datetime,
    duration: float,
    extracted: int,
    transformed: int,
    loaded: int,
    errors: list[str],
    status: str = "success",
) -> dict:
    return {
        "run_id":            run_id,
        "pipeline_name":     phase,
        "phase":             phase,
        "started_at":        started,
        "finished_at":       datetime.utcnow(),
        "status":            status,
        "records_extracted": extracted,
        "records_transformed": transformed,
        "records_loaded":    loaded,
        "errors_count":      len(errors),
        "error_details":     "\n".join(errors) if errors else None,
        "duration_seconds":  duration,
    }


if __name__ == "__main__":
    main()
