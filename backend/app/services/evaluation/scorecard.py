import os
import json
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/synthetic"))

def evaluate_engine():
    print("Loading results and ground truth...\n")
    
    # Load System Results and Ground Truth
    results_df = pd.read_csv(os.path.join(DATA_DIR, "reconciliation_results.csv"))
    
    with open(os.path.join(DATA_DIR, "ground_truth.json"), "r") as f:
        gt_data = json.load(f)
    gt_df = pd.DataFrame(gt_data)
    
    # Merge on canonical_id to compare System vs Reality
    eval_df = pd.merge(results_df, gt_df, on="canonical_id")
    
    y_true = eval_df['expected_status']
    y_pred = eval_df['system_status']
    
    # Calculate ML Metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='weighted', zero_division=0
    )
    
    print("--- 📊 MODEL EVALUATION SCORECARD ---")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall:    {recall * 100:.2f}%")
    print(f"F1 Score:  {f1 * 100:.2f}%\n")
    
    print("--- 🔍 DETAILED BREAKDOWN ---")
    
    # Calculate exact failure types
    true_matches = len(eval_df[(eval_df['expected_status'] == 'MATCH') & (eval_df['system_status'] == 'MATCH')])
    false_matches = eval_df[(eval_df['expected_status'] != 'MATCH') & (eval_df['system_status'] == 'MATCH')]
    
    print(f"True Matches:       {true_matches}")
    print(f"False Matches:      {len(false_matches)}")
    print(f"Exceptions Handled: {len(eval_df[eval_df['system_status'] == 'EXCEPTION'])}")
    
    print("\n⚠️ Root Cause of False Matches:")
    if not false_matches.empty:
        reasons = false_matches['expected_reason'].value_counts()
        for reason, count in reasons.items():
            print(f" - {count} records: {reason}")

if __name__ == "__main__":
    evaluate_engine()