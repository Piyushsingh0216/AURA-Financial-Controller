import os
import re
from typing import Optional

import pandas as pd


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/synthetic"))

# Bank statements commonly use different labels for the same information. The
# keys below are matched after case/whitespace/punctuation normalization, so
# values such as "Transaction ID", "transaction_id", and "Transaction-ID"
# are treated identically.
BANK_COLUMN_ALIASES = {
    "bank_stmt_id": (
        "bank_stmt_id",
        "bank_statement_id",
        "statement_id",
        "transaction_id",
        "transaction_reference",
        "transaction_reference_number",
        "txn_id",
        "txn_reference",
        "reference_id",
        "reference_number",
        "reference_no",
        "utr",
        "utr_number",
    ),
    "description": (
        "description",
        "memo",
        "narration",
        "particulars",
        "details",
        "remarks",
        "transaction_description",
        "transaction_details",
    ),
    "credit_amount": (
        "credit_amount",
        "credit",
        "credit_value",
        "credit_amt",
        "amount",
        "transaction_amount",
        "txn_amount",
        "deposit",
        "deposit_amount",
        "paid_in",
        "paid_in_amount",
        "cr_amount",
        "amount_inr",
        "credit_amount_inr",
    ),
    "canonical_id": ("canonical_id", "canonical_identifier"),
    "invoice_ref": (
        "invoice_ref",
        "invoice_reference",
        "invoice_id",
        "invoice_number",
        "invoice_no",
    ),
}

RESULT_COLUMNS = [
    "bank_stmt_id",
    "invoice_ref",
    "system_status",
    "system_reason",
    "confidence",
    "canonical_id",
]


def _header_key(header: object) -> str:
    """Create a comparison key independent of case, spacing, and punctuation."""
    return re.sub(r"[^a-z0-9]", "", str(header).strip().lower())


def _unique_normalized_headers(columns: pd.Index) -> list[str]:
    """Lowercase/trim headers and make duplicate labels safe to address."""
    seen: dict[str, int] = {}
    normalized: list[str] = []

    for column in columns:
        # This deliberately mirrors the basic normalization expected for bank
        # CSVs while retaining enough information for alias matching below.
        base = str(column).strip().lower() or "unnamed_column"
        count = seen.get(base, 0)
        seen[base] = count + 1
        normalized.append(base if count == 0 else f"{base}__{count + 1}")

    return normalized


def _blank_mask(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip()
    return (
        series.isna()
        | values.fillna("").eq("")
        | values.fillna("").str.lower().isin({"nan", "none", "null", "nat"})
    ).fillna(True)


def _clean_string_series(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip().fillna("")
    return values.mask(values.str.lower().isin({"nan", "none", "null", "nat"}), "")


def _unique_bank_ids(bank_ids: pd.Series) -> pd.Series:
    """Keep 3D node keys and subsequent AI lookups unambiguous."""
    seen: dict[str, int] = {}
    unique_ids: list[str] = []

    for value in bank_ids.astype("string").tolist():
        base_id = str(value)
        occurrence = seen.get(base_id, 0)
        seen[base_id] = occurrence + 1
        unique_ids.append(base_id if occurrence == 0 else f"{base_id}-{occurrence + 1}")

    return pd.Series(unique_ids, index=bank_ids.index, dtype="string")


def _source_series(dataframe: pd.DataFrame, aliases: tuple[str, ...]) -> Optional[pd.Series]:
    """Return the first non-empty value across known aliases, if one exists."""
    positions: dict[str, int] = {}
    for position, column in enumerate(dataframe.columns):
        positions.setdefault(_header_key(column), position)

    selected: Optional[pd.Series] = None
    for alias in aliases:
        position = positions.get(_header_key(alias))
        if position is None:
            continue

        candidate = dataframe.iloc[:, position].copy()
        if selected is None:
            selected = candidate
        else:
            selected = selected.where(~_blank_mask(selected), candidate)

    return selected


def _coerce_amounts(series: Optional[pd.Series], index: pd.Index) -> pd.Series:
    """Convert common CSV money formats to numbers; missing values become zero."""
    if series is None:
        return pd.Series(0.0, index=index, dtype="float64")

    values = series.astype("string").fillna("").str.strip()
    values = values.str.replace(",", "", regex=False)
    values = values.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    values = values.str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(values, errors="coerce").fillna(0.0).astype("float64")


def normalize_bank_dataframe(bank_df: pd.DataFrame) -> pd.DataFrame:
    """Return a bank dataframe with the engine's required columns present.

    Uploaded statements are allowed to omit fields or use a familiar banking
    synonym. Missing IDs are generated deterministically by row position,
    descriptions default to an empty string, amounts default to zero, and
    canonical IDs fall back to the bank statement ID. This keeps an unfamiliar
    header from becoming a KeyError later in the reconciliation or AI flow.
    """
    normalized = bank_df.copy()
    normalized.columns = _unique_normalized_headers(normalized.columns)

    generated_ids = pd.Series(
        [f"UPL-{row_number:06d}" for row_number in range(1, len(normalized) + 1)],
        index=normalized.index,
        dtype="string",
    )

    bank_id_source = _source_series(normalized, BANK_COLUMN_ALIASES["bank_stmt_id"])
    if bank_id_source is None:
        bank_ids = generated_ids
    else:
        bank_ids = _clean_string_series(bank_id_source)
        bank_ids = bank_ids.mask(_blank_mask(bank_ids), generated_ids)
    bank_ids = _unique_bank_ids(bank_ids)

    description_source = _source_series(normalized, BANK_COLUMN_ALIASES["description"])
    descriptions = (
        _clean_string_series(description_source)
        if description_source is not None
        else pd.Series("", index=normalized.index, dtype="string")
    )

    canonical_source = _source_series(normalized, BANK_COLUMN_ALIASES["canonical_id"])
    if canonical_source is None:
        canonical_ids = bank_ids.copy()
    else:
        canonical_ids = _clean_string_series(canonical_source)
        canonical_ids = canonical_ids.mask(_blank_mask(canonical_ids), bank_ids)

    invoice_source = _source_series(normalized, BANK_COLUMN_ALIASES["invoice_ref"])
    invoice_refs = (
        _clean_string_series(invoice_source)
        if invoice_source is not None
        else pd.Series("", index=normalized.index, dtype="string")
    )

    normalized["bank_stmt_id"] = bank_ids
    normalized["description"] = descriptions
    normalized["credit_amount"] = _coerce_amounts(
        _source_series(normalized, BANK_COLUMN_ALIASES["credit_amount"]), normalized.index
    )
    normalized["canonical_id"] = canonical_ids
    normalized["invoice_ref"] = invoice_refs

    return normalized


class BaselineReconciliationEngine:
    def __init__(self, bank_records_path: Optional[str] = None):
        print("Loading datasets...")
        bank_path = bank_records_path or os.path.join(DATA_DIR, "bank_records.csv")
        self.bank_df = normalize_bank_dataframe(pd.read_csv(bank_path))
        self.gateway_df = pd.read_csv(os.path.join(DATA_DIR, "gateway_records.csv"))
        self.invoice_df = pd.read_csv(os.path.join(DATA_DIR, "invoice_records.csv"))

    def normalize_data(self):
        print("Normalizing text, dates, and extracting references...")

        # Normalize once more immediately before processing. It is harmless
        # for already-normalized data and protects callers that replace
        # self.bank_df after construction.
        self.bank_df = normalize_bank_dataframe(self.bank_df)

        # 1. Extract Invoice Reference from Bank Description
        # e.g., "UPI/NEFT/TATA CONSU/INV-2026-2001" -> "INV-2026-2001"
        extracted_refs = self.bank_df["description"].apply(
            lambda value: match.group(0).upper()
            if (match := re.search(r"INV-\d{4}-\d{4}", str(value), re.IGNORECASE))
            else ""
        )
        explicit_refs = _clean_string_series(self.bank_df["invoice_ref"]).str.upper()
        self.bank_df["extracted_invoice_ref"] = explicit_refs.mask(
            _blank_mask(explicit_refs), extracted_refs
        )

        # 2. Normalize Text for Fuzzy Matching
        def clean_text(text):
            if pd.isna(text):
                return ""
            return re.sub(r"[^a-z0-9\s]", "", str(text).lower().strip())

        self.invoice_df["norm_customer"] = self.invoice_df["customer_name"].apply(clean_text)
        self.gateway_df["norm_customer"] = self.gateway_df["customer_name"].apply(clean_text)

    def run_reconciliation(self):
        self.normalize_data()
        print("Running rules-based matching engine...\n")

        results = []

        # We iterate through the Bank Statement as our anchor (cash is king)
        for _, bank_row in self.bank_df.iterrows():
            bank_id = bank_row["bank_stmt_id"]
            inv_ref = bank_row["extracted_invoice_ref"]
            bank_amount = bank_row["credit_amount"]
            canonical_id = bank_row["canonical_id"]  # Kept for evaluation scoring later

            status = "UNRESOLVED"
            reason = "No matching logic triggered"
            match_confidence = 0.0

            # Step 1: Find related records
            inv_matches = self.invoice_df[self.invoice_df["invoice_id"] == inv_ref]
            gw_matches = self.gateway_df[self.gateway_df["invoice_ref"] == inv_ref]

            # Step 2: Rule - Missing Invoice
            if not inv_ref:
                status = "EXCEPTION"
                reason = "Invoice reference missing from bank description"
                match_confidence = 0.0
            elif inv_matches.empty:
                status = "EXCEPTION"
                reason = "Invoice missing in ERP"
                match_confidence = 0.0
            else:
                inv_row = inv_matches.iloc[0]
                inv_amount = inv_row["amount"]

                # Step 3: Rule - Duplicate Gateway Transactions
                if len(gw_matches) > 1:
                    status = "DUPLICATE"
                    reason = f"Found {len(gw_matches)} gateway transactions for this invoice"
                    match_confidence = 0.99

                # Step 4: Rule - Check Gateway Match & Fees FIRST
                elif not gw_matches.empty:
                    gw_row = gw_matches.iloc[0]
                    gw_amount = gw_row["settled_amount"]
                    expected_fee = round(inv_amount * 0.02, 2)

                    # If gateway matches the expected fee deduction
                    if abs((inv_amount - expected_fee) - gw_amount) < 1.0:
                        status = "REVIEW"
                        reason = f"Gateway amount mismatch due to fee deduction (â‚¹{round(inv_amount - gw_amount, 2)})"
                        match_confidence = 0.85
                    elif bank_amount == inv_amount:
                        status = "MATCH"
                        reason = "Exact match across sources"
                        match_confidence = 1.0
                    else:
                        status = "EXCEPTION"
                        reason = f"Amount mismatch: Bank(â‚¹{bank_amount}) vs Invoice(â‚¹{inv_amount})"
                        match_confidence = 0.50

                # Step 5: Rule - Exact Amount Match (No Gateway)
                elif bank_amount == inv_amount:
                    status = "MATCH"
                    reason = "Exact match across sources"
                    match_confidence = 1.0

            results.append(
                {
                    "bank_stmt_id": bank_id,
                    "invoice_ref": inv_ref,
                    "system_status": status,
                    "system_reason": reason,
                    "confidence": match_confidence,
                    "canonical_id": canonical_id,  # For our evaluation metric calculation
                }
            )

        return pd.DataFrame(results, columns=RESULT_COLUMNS)


if __name__ == "__main__":
    engine = BaselineReconciliationEngine()
    results_df = engine.run_reconciliation()

    # Save the reconciliation output
    output_path = os.path.join(DATA_DIR, "reconciliation_results.csv")
    results_df.to_csv(output_path, index=False)

    # Display summary
    print("--- AUTOMATED ENGINE RESULTS ---")
    print(results_df["system_status"].value_counts())
    print(f"\nResults saved to {output_path}")
