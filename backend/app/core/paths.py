import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_CANDIDATES = (
    BACKEND_DIR / "data" / "synthetic",
    BACKEND_DIR.parent / "data" / "synthetic",
)


def resolve_data_dir() -> Path:
    """Resolve the reference-data directory for local and container layouts."""
    configured_dir = os.getenv("AURA_DATA_DIR")
    if configured_dir:
        return Path(configured_dir).expanduser().resolve()

    return next(
        (candidate for candidate in DATA_CANDIDATES if candidate.is_dir()),
        DATA_CANDIDATES[0],
    )


DATA_DIR = resolve_data_dir()
BANK_RECORDS_PATH = DATA_DIR / "bank_records.csv"
RECONCILIATION_RESULTS_PATH = DATA_DIR / "reconciliation_results.csv"
GATEWAY_RECORDS_PATH = DATA_DIR / "gateway_records.csv"
INVOICE_RECORDS_PATH = DATA_DIR / "invoice_records.csv"
