import os
import json
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

fake = Faker('en_IN')  # Using Indian locale for realistic enterprise data
Faker.seed(42)
random.seed(42)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/synthetic"))
os.makedirs(DATA_DIR, exist_ok=True)

def generate_multi_source_data(n_canonical=150):
    canonical_records = []
    bank_records = []
    gateway_records = []
    invoice_records = []

    companies = [
        "Tata Consultancy Services", "Infosys Limited", "Wipro Enterprises", 
        "Reliance Digital", "HCL Technologies", "Zomato Logistics", 
        "Swiggy Tech Fleet", "Paytm Merchant Services", "Razorpay Corp", 
        "Flipkart Internet Pvt Ltd", "Zoho Corporation", "Freshworks India"
    ]

    base_date = datetime(2026, 8, 1)

    for i in range(1, n_canonical + 1):
        canonical_id = f"CANON-{1000 + i}"
        customer = random.choice(companies)
        amount = round(random.uniform(5000.0, 250000.0), 2)
        txn_date = base_date + timedelta(days=random.randint(0, 25))
        invoice_ref = f"INV-2026-{2000 + i}"
        
        # Anomaly scenario distribution
        scenario = random.choices(
            ["perfect_match", "minor_typo", "gateway_fee_mismatch", "missing_invoice", "duplicate_gateway"],
            weights=[0.65, 0.15, 0.10, 0.05, 0.05]
        )[0]

        # Ground truth status tracking
        truth_status = "MATCH"
        expected_reason = "Exact match across sources"

        # 1. Generate Invoice Record
        if scenario != "missing_invoice":
            inv_customer = customer
            if scenario == "minor_typo":
                inv_customer = customer.replace("Limited", "Ltd").replace("Enterprises", "Ent").replace("Technologies", "Tech")
            
            invoice_records.append({
                "invoice_id": invoice_ref,
                "customer_name": inv_customer,
                "amount": amount,
                "due_date": (txn_date + timedelta(days=15)).strftime("%Y-%m-%d"),
                "canonical_id": canonical_id
            })
        else:
            truth_status = "EXCEPTION"
            expected_reason = "Invoice missing in ERP"

        # 2. Generate Payment Gateway Record
        gw_amount = amount
        if scenario == "gateway_fee_mismatch":
            fee = round(amount * 0.02, 2)  # 2% gateway processing fee deducted
            gw_amount = round(amount - fee, 2)
            truth_status = "REVIEW"
            expected_reason = f"Gateway amount mismatch due to fee deduction (₹{fee})"

        gw_record = {
            "gateway_txn_id": f"pay_{uuid.uuid4().hex[:12]}",
            "invoice_ref": invoice_ref,
            "customer_name": customer,
            "settled_amount": gw_amount,
            "status": "SUCCESS",
            "timestamp": (txn_date + timedelta(hours=random.randint(1, 4))).strftime("%Y-%m-%d %H:%M:%S"),
            "canonical_id": canonical_id
        }
        gateway_records.append(gw_record)

        if scenario == "duplicate_gateway":
            truth_status = "DUPLICATE"
            expected_reason = "Duplicate gateway transaction detected"
            dup_record = gw_record.copy()
            dup_record["gateway_txn_id"] = f"pay_{uuid.uuid4().hex[:12]}"
            dup_record["timestamp"] = (txn_date + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
            gateway_records.append(dup_record)

        # 3. Generate Bank Statement Record
        bank_records.append({
            "bank_stmt_id": f"BNK-{txn_date.strftime('%Y%m')}-{3000 + i}",
            "description": f"UPI/NEFT/{customer[:10].upper()}/{invoice_ref}",
            "credit_amount": amount,
            "value_date": (txn_date + timedelta(days=random.randint(0, 2))).strftime("%Y-%m-%d"),
            "canonical_id": canonical_id
        })

        canonical_records.append({
            "canonical_id": canonical_id,
            "expected_status": truth_status,
            "expected_reason": expected_reason,
            "base_amount": amount,
            "customer": customer,
            "invoice_ref": invoice_ref
        })

    # Save outputs
    df_bank = pd.DataFrame(bank_records)
    df_gateway = pd.DataFrame(gateway_records)
    df_invoice = pd.DataFrame(invoice_records)

    df_bank.to_csv(os.path.join(DATA_DIR, "bank_records.csv"), index=False)
    df_gateway.to_csv(os.path.join(DATA_DIR, "gateway_records.csv"), index=False)
    df_invoice.to_csv(os.path.join(DATA_DIR, "invoice_records.csv"), index=False)

    with open(os.path.join(DATA_DIR, "ground_truth.json"), "w") as f:
        json.dump(canonical_records, f, indent=2)

    return df_bank, df_gateway, df_invoice, canonical_records

if __name__ == "__main__":
    b, g, i, gt = generate_multi_source_data(150)
    print(f"Data Generation Completed successfully!")
    print(f"Bank Records: {len(b)} rows")
    print(f"Gateway Records: {len(g)} rows")
    print(f"Invoice Records: {len(i)} rows")
    print(f"Ground Truth Entries: {len(gt)}")
    
    # Show breakdown of expected statuses
    status_counts = pd.DataFrame(gt)["expected_status"].value_counts().to_dict()
    print("\nGround Truth Distribution:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count} ({round(count/len(gt)*100, 1)}%)")