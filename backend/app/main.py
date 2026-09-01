from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import os

from app.services.reconciliation.engine import BaselineReconciliationEngine
from app.services.ai.agent import investigate_exception
from fastapi.responses import FileResponse


app = FastAPI(title="AURA Finance Controller API")

# Allow your React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/synthetic"))

@app.get("/")
def health_check():
    return {"status": "AURA Systems Online"}

@app.post("/api/v1/reconcile")
def run_batch_reconciliation():
    """Runs Layer 1: Deterministic Engine"""
    engine = BaselineReconciliationEngine()
    results_df = engine.run_reconciliation()
    
    # Save results
    output_path = os.path.join(DATA_DIR, "reconciliation_results.csv")
    results_df.to_csv(output_path, index=False)
    
    # Calculate summary metrics
    total = len(results_df)
    matched = len(results_df[results_df['system_status'] == 'MATCH'])
    exceptions = len(results_df[results_df['system_status'] == 'EXCEPTION'])
    reviews = len(results_df[results_df['system_status'] == 'REVIEW'])
    duplicates = len(results_df[results_df['system_status'] == 'DUPLICATE'])
    
    return {
        "metrics": {
            "total_records": total,
            "matched": matched,
            "exceptions": exceptions,
            "reviews": reviews,
            "duplicates": duplicates,
            "accuracy": round((matched / total) * 100, 2) if total > 0 else 0
        },
        "message": "Batch reconciliation complete."
    }

@app.get("/api/v1/exceptions")
def get_exceptions():
    """Fetches all non-matching records for the Exception Cockpit"""
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, "reconciliation_results.csv"))
        exceptions_df = df[df['system_status'].isin(['REVIEW', 'EXCEPTION', 'DUPLICATE'])]
        return exceptions_df.to_dict(orient="records")
    except Exception as e:
        return {"error": "Reconciliation not run yet."}

@app.post("/api/v1/investigate/{bank_stmt_id}")
def run_ai_investigation(bank_stmt_id: str):
    """Runs Layer 3: AI Investigation on a specific transaction"""
    # Load datasets to find the context
    results_df = pd.read_csv(os.path.join(DATA_DIR, "reconciliation_results.csv"))
    bank_df = pd.read_csv(os.path.join(DATA_DIR, "bank_records.csv"))
    
    record = results_df[results_df['bank_stmt_id'] == bank_stmt_id]
    if record.empty:
        return {"error": "Transaction not found."}
        
    system_reason = record.iloc[0]['system_reason']
    
    # Extract the raw bank data for the prompt
    bank_raw = bank_df[bank_df['bank_stmt_id'] == bank_stmt_id].to_dict(orient="records")[0]
    
    # Call our LLM Agent
    ai_decision = investigate_exception(
        bank_record=str(bank_raw),
        invoice_record="Context fetched from ERP...", 
        gateway_record="Context fetched from Gateway...",
        system_reason=system_reason
    )
    
    return {
        "transaction_id": bank_stmt_id,
        "ai_analysis": ai_decision
    }




@app.post("/api/v1/investigate/{bank_stmt_id}")
def run_ai_investigation(bank_stmt_id: str, simulate_outage: bool = False):
    """Runs Layer 3 with a built-in Chaos Monkey trigger"""
    results_df = pd.read_csv(os.path.join(DATA_DIR, "reconciliation_results.csv"))
    bank_df = pd.read_csv(os.path.join(DATA_DIR, "bank_records.csv"))
    
    record = results_df[results_df['bank_stmt_id'] == bank_stmt_id]
    if record.empty:
        return {"error": "Transaction not found."}
        
    # CHAOS MONKEY: Force the fallback mode instantly
    if simulate_outage:
        return {
            "transaction_id": bank_stmt_id,
            "ai_analysis": {
                "investigation_summary": "AI analysis unavailable. Fallback to rule-based analysis. Error: 503 - SIMULATED_INFRASTRUCTURE_OUTAGE",
                "recommended_action": "MANUAL_REVIEW_REQUIRED",
                "risk_level": "HIGH"
            }
        }

    system_reason = record.iloc[0]['system_reason']
    bank_raw = bank_df[bank_df['bank_stmt_id'] == bank_stmt_id].to_dict(orient="records")[0]
    
    ai_decision = investigate_exception(str(bank_raw), "Context...", "Context...", system_reason)
    return {"transaction_id": bank_stmt_id, "ai_analysis": ai_decision}

@app.get("/api/v1/export")
def export_audit_trail():
    """Generates the downloadable CSV Audit Report"""
    file_path = os.path.join(DATA_DIR, "reconciliation_results.csv")
    return FileResponse(path=file_path, filename="aura_audit_trail.csv", media_type="text/csv")