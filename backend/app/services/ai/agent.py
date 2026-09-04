import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def _groq_client() -> OpenAI:
    """Create the optional Groq client only when an investigation needs it."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    # The OpenAI-compatible client is pointed at Groq's API for inference.
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

def investigate_exception(bank_record, invoice_record, gateway_record, system_reason):
    """
    Takes financial records and asks the LLM to explain the discrepancy 
    and recommend a bounded action.
    """
    prompt = f"""
    You are an AI Finance Controller analyzing a transaction exception.
    
    EVIDENCE:
    - Bank Record: {bank_record}
    - Invoice Record: {invoice_record}
    - Gateway Record: {gateway_record}
    - System Flag: {system_reason}
    
    TASK:
    Analyze the discrepancy. Provide a highly professional, concise explanation and one of the following recommended actions: 
    [MANUAL_REVIEW_REQUIRED, APPROVE_FEE_DEDUCTION, REQUEST_NEW_INVOICE]
    
    Respond ONLY in valid JSON format matching this schema:
    {{
        "investigation_summary": "string explaining the exact mathematical difference and likely cause",
        "recommended_action": "string from the allowed list",
        "risk_level": "LOW, MEDIUM, or HIGH"
    }}
    """
    
    try:
        response = _groq_client().chat.completions.create(
            model="qwen/qwen3.8-27b", # Switched to available Qwen model
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        # Graceful Failure Mode (Crucial for the competition)
        return {
            "investigation_summary": f"AI analysis unavailable. Fallback to rule-based analysis. Error: {str(e)}",
            "recommended_action": "MANUAL_REVIEW_REQUIRED",
            "risk_level": "HIGH"
        }

if __name__ == "__main__":
    # Test the agent with dummy data
    test_result = investigate_exception(
        bank_record="Bank: ₹980.00 received",
        invoice_record="Invoice: ₹1000.00 billed to Tata Consultancy",
        gateway_record="Gateway: ₹980.00 settled (₹20.00 fee)",
        system_reason="Gateway amount mismatch due to fee deduction"
    )
    print(json.dumps(test_result, indent=2))
