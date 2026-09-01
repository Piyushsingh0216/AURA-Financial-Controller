import os
import re
import pandas as pd
from rapidfuzz import fuzz

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/synthetic"))

class BaselineReconciliationEngine:
    def __init__(self):
        print("Loading datasets...")
        self.bank_df = pd.read_csv(os.path.join(DATA_DIR, "bank_records.csv"))
        self.gateway_df = pd.read_csv(os.path.join(DATA_DIR, "gateway_records.csv"))
        self.invoice_df = pd.read_csv(os.path.join(DATA_DIR, "invoice_records.csv"))
        
    def normalize_data(self):
        print("Normalizing text, dates, and extracting references...")
        
        # 1. Extract Invoice Reference from Bank Description
        # e.g., "UPI/NEFT/TATA CONSU/INV-2026-2001" -> "INV-2026-2001"
        self.bank_df['extracted_invoice_ref'] = self.bank_df['description'].apply(
            lambda x: match.group(0) if (match := re.search(r'INV-\d{4}-\d{4}', str(x))) else None
        )
        
        # 2. Normalize Text for Fuzzy Matching
        def clean_text(text):
            if pd.isna(text): return ""
            return re.sub(r'[^a-z0-9\s]', '', str(text).lower().strip())
            
        self.invoice_df['norm_customer'] = self.invoice_df['customer_name'].apply(clean_text)
        self.gateway_df['norm_customer'] = self.gateway_df['customer_name'].apply(clean_text)

    def run_reconciliation(self):
        self.normalize_data()
        print("Running rules-based matching engine...\n")
        
        results = []
        
        # We iterate through the Bank Statement as our anchor (cash is king)
        for _, bank_row in self.bank_df.iterrows():
            bank_id = bank_row['bank_stmt_id']
            inv_ref = bank_row['extracted_invoice_ref']
            bank_amount = bank_row['credit_amount']
            canonical_id = bank_row['canonical_id'] # Kept for evaluation scoring later
            
            status = "UNRESOLVED"
            reason = "No matching logic triggered"
            match_confidence = 0.0
            
            # Step 1: Find related records
            inv_matches = self.invoice_df[self.invoice_df['invoice_id'] == inv_ref]
            gw_matches = self.gateway_df[self.gateway_df['invoice_ref'] == inv_ref]
            
            # Step 2: Rule - Missing Invoice
            if inv_matches.empty:
                status = "EXCEPTION"
                reason = "Invoice missing in ERP"
                match_confidence = 0.0
            else:
                inv_row = inv_matches.iloc[0]
                inv_amount = inv_row['amount']
                
                # Step 3: Rule - Duplicate Gateway Transactions
                if len(gw_matches) > 1:
                    status = "DUPLICATE"
                    reason = f"Found {len(gw_matches)} gateway transactions for this invoice"
                    match_confidence = 0.99
                
                # Step 4: Rule - Check Gateway Match & Fees FIRST
                elif not gw_matches.empty:
                    gw_row = gw_matches.iloc[0]
                    gw_amount = gw_row['settled_amount']
                    expected_fee = round(inv_amount * 0.02, 2)
                    
                    # If gateway matches the expected fee deduction
                    if abs((inv_amount - expected_fee) - gw_amount) < 1.0:
                        status = "REVIEW"
                        reason = f"Gateway amount mismatch due to fee deduction (₹{round(inv_amount - gw_amount, 2)})"
                        match_confidence = 0.85
                    elif bank_amount == inv_amount:
                        status = "MATCH"
                        reason = "Exact match across sources"
                        match_confidence = 1.0
                    else:
                        status = "EXCEPTION"
                        reason = f"Amount mismatch: Bank(₹{bank_amount}) vs Invoice(₹{inv_amount})"
                        match_confidence = 0.50
                        
                # Step 5: Rule - Exact Amount Match (No Gateway)
                elif bank_amount == inv_amount:
                    status = "MATCH"
                    reason = "Exact match across sources"
                    match_confidence = 1.0
                        
            results.append({
                "bank_stmt_id": bank_id,
                "invoice_ref": inv_ref,
                "system_status": status,
                "system_reason": reason,
                "confidence": match_confidence,
                "canonical_id": canonical_id # For our evaluation metric calculation
            })
            
        result_df = pd.DataFrame(results)
        return result_df

if __name__ == "__main__":
    engine = BaselineReconciliationEngine()
    results_df = engine.run_reconciliation()
    
    # Save the reconciliation output
    output_path = os.path.join(DATA_DIR, "reconciliation_results.csv")
    results_df.to_csv(output_path, index=False)
    
    # Display summary
    print("--- AUTOMATED ENGINE RESULTS ---")
    print(results_df['system_status'].value_counts())
    print(f"\nResults saved to {output_path}")