"""
Test a sample claim against the API.

Usage:
    python scripts/test_claim.py [claim_file]

Defaults to data/claims/claim_001_approved.json
"""

import json
import sys
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
DEFAULT_CLAIM = Path(__file__).resolve().parents[1] / "data" / "claims" / "claim_001_approved.json"


def main() -> None:
    claim_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CLAIM

    if not claim_file.exists():
        print(f"Error: Claim file not found: {claim_file}")
        sys.exit(1)

    with open(claim_file) as f:
        claim = json.load(f)

    print(f"Submitting claim: {claim['claim_id']}")
    print(f"  Employee: {claim['employee_name']}")
    print(f"  Amount: ${claim['total_claimed_amount']:,.2f}")
    print(f"  Destination: {claim.get('destination', 'N/A')}")
    print()

    try:
        response = httpx.post(f"{BASE_URL}/evaluate", json=claim, timeout=120)
        response.raise_for_status()
        result = response.json()

        print("=" * 60)
        print(f"Decision:   {result['decision'].upper()}")
        print(f"Approved:   ${result['approved_amount']:,.2f}")
        print(f"Rejected:   ${result['rejected_amount']:,.2f}")
        print(f"Confidence: {result['confidence_score']:.0%}")
        print(f"Tools Used: {', '.join(result['tools_used'])}")
        print()

        if result["deductions"]:
            print("Deductions:")
            for d in result["deductions"]:
                print(f"  - {d['expense_type']}: ${d['deducted_amount']:,.2f} — {d['reason']}")
            print()

        if result["missing_documents"]:
            print("Missing Documents:")
            for doc in result["missing_documents"]:
                print(f"  - {doc}")
            print()

        print(f"Reasoning: {result['reasoning'][:300]}")
        print("=" * 60)

        # Save output
        out_file = claim_file.parent.parent / "sample_outputs" / f"api_output_{claim_file.stem}.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull output saved to: {out_file}")

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}")
    except httpx.ConnectError:
        print(f"Cannot connect to {BASE_URL} — is the server running?")


if __name__ == "__main__":
    main()
