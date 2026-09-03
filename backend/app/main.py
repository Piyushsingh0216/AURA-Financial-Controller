import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pandas.errors import EmptyDataError, ParserError

from app.services.ai.agent import investigate_exception
from app.services.reconciliation.engine import (
    BaselineReconciliationEngine,
    normalize_bank_dataframe,
)


app = FastAPI(title="AURA Finance Controller API")

# Allow the React frontend to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/synthetic"))
BANK_RECORDS_PATH = os.path.join(DATA_DIR, "bank_records.csv")
RECONCILIATION_RESULTS_PATH = os.path.join(DATA_DIR, "reconciliation_results.csv")


def _metrics_for(results_df: pd.DataFrame) -> dict[str, int | float]:
    """Build the metrics shape consumed by the existing dashboard."""
    status_counts = results_df["system_status"].value_counts()
    total = len(results_df)
    matched = int(status_counts.get("MATCH", 0))

    return {
        "total_records": total,
        "matched": matched,
        "exceptions": int(status_counts.get("EXCEPTION", 0)),
        "reviews": int(status_counts.get("REVIEW", 0)),
        "duplicates": int(status_counts.get("DUPLICATE", 0)),
        "accuracy": round((matched / total) * 100, 2) if total else 0,
    }


def _run_reconciliation(message: str) -> dict:
    """Run the deterministic engine and persist the audit results."""
    engine = BaselineReconciliationEngine()
    results_df = engine.run_reconciliation()
    results_df.to_csv(RECONCILIATION_RESULTS_PATH, index=False)

    return {"metrics": _metrics_for(results_df), "message": message}


@app.get("/")
def health_check():
    return {"status": "AURA Systems Online"}


@app.post("/api/v1/reconcile")
def run_batch_reconciliation():
    """Runs Layer 1: Deterministic Engine."""
    return _run_reconciliation("Batch reconciliation complete.")


@app.post("/api/v1/reconcile/upload")
async def upload_bank_statement(file: UploadFile = File(...)):
    """Replace the active bank statement with a CSV and reconcile it."""
    if not file.filename or Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Please upload a .csv bank statement.")

    temporary_path: str | None = None
    try:
        # Write and parse a temporary file before replacing the active data, so
        # an unreadable/empty upload cannot corrupt the current bank statement.
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=DATA_DIR, prefix=".bank-upload-", suffix=".csv"
        ) as temporary_file:
            temporary_path = temporary_file.name
            shutil.copyfileobj(file.file, temporary_file)

        try:
            # Parse the complete file before replacing the active statement.
            # Checking only the header can miss a malformed row later in a
            # larger CSV and leave the active data in a broken state.
            pd.read_csv(temporary_path)
        except (EmptyDataError, ParserError, UnicodeDecodeError, ValueError) as error:
            raise HTTPException(
                status_code=400, detail="The uploaded file is not a readable CSV."
            ) from error

        os.replace(temporary_path, BANK_RECORDS_PATH)
        temporary_path = None
        return _run_reconciliation("Bank statement uploaded and reconciliation complete.")
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
        await file.close()


@app.get("/api/v1/exceptions")
def get_exceptions():
    """Fetch all non-matching records for the Exception Cockpit."""
    try:
        df = pd.read_csv(RECONCILIATION_RESULTS_PATH)
        exceptions_df = df[df["system_status"].isin(["REVIEW", "EXCEPTION", "DUPLICATE"])]
        return exceptions_df.to_dict(orient="records")
    except (FileNotFoundError, EmptyDataError, KeyError):
        # The frontend expects a collection it can render, including before the
        # first reconciliation run.
        return []


@app.post("/api/v1/investigate/{bank_stmt_id}")
def run_ai_investigation(bank_stmt_id: str, simulate_outage: bool = False):
    """Run Layer 3 analysis, with a deterministic Chaos Monkey fallback."""
    try:
        results_df = pd.read_csv(RECONCILIATION_RESULTS_PATH)
    except (FileNotFoundError, EmptyDataError):
        return {"error": "Reconciliation not run yet."}

    if "bank_stmt_id" not in results_df.columns:
        return {"error": "Reconciliation results are invalid."}

    record = results_df[results_df["bank_stmt_id"].astype("string") == bank_stmt_id]
    if record.empty:
        return {"error": "Transaction not found."}

    # CHAOS MONKEY: force the fallback mode without trying to load bank data.
    if simulate_outage:
        return {
            "transaction_id": bank_stmt_id,
            "ai_analysis": {
                "investigation_summary": "AI analysis unavailable. Fallback to rule-based analysis. Error: 503 - SIMULATED_INFRASTRUCTURE_OUTAGE",
                "recommended_action": "MANUAL_REVIEW_REQUIRED",
                "risk_level": "HIGH",
            },
        }

    system_reason = str(record.iloc[0].get("system_reason", "Transaction requires review."))
    try:
        # Reuse the exact same normalization used by reconciliation. This is
        # essential for uploads with headers such as "Transaction ID" or
        # "Memo ", which otherwise break the AI lookup with a KeyError.
        bank_df = normalize_bank_dataframe(pd.read_csv(BANK_RECORDS_PATH))
        bank_records = bank_df[bank_df["bank_stmt_id"] == bank_stmt_id]
        bank_raw = (
            bank_records.iloc[0].to_dict()
            if not bank_records.empty
            else {"bank_stmt_id": bank_stmt_id, "record_lookup": "not found"}
        )
    except (FileNotFoundError, EmptyDataError, ParserError, UnicodeDecodeError, ValueError):
        bank_raw = {"bank_stmt_id": bank_stmt_id, "record_lookup": "unavailable"}

    ai_decision = investigate_exception(
        bank_record=str(bank_raw),
        invoice_record="Context fetched from ERP...",
        gateway_record="Context fetched from Gateway...",
        system_reason=system_reason,
    )
    return {"transaction_id": bank_stmt_id, "ai_analysis": ai_decision}


@app.get("/api/v1/export")
def export_audit_trail():
    """Generates the downloadable CSV Audit Report."""
    return FileResponse(
        path=RECONCILIATION_RESULTS_PATH,
        filename="aura_audit_trail.csv",
        media_type="text/csv",
    )
