import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.verification_agent import run_verification


# ============================================================
# 1. LOAD ACTUAL RBI EVIDENCE
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

CHUNKS_FILE = (
    ROOT / "documents" / "processed" / "rbi_chunks.json"
)

with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
    RBI_RECORDS = json.load(file)


def get_evidence(source, page, status="historical"):
    """
    Retrieve an actual source/page record from the local database.
    """

    for record in RBI_RECORDS:

        if (
            record.get("source") == source
            and record.get("page_number") == page
        ):

            return {
                "source": source,
                "page": page,
                "status": status,
                "scope": "evaluation",
                "chunk_type": "original_chunk",
                "text": record.get("text", "")
            }

    raise ValueError(
        f"Evidence not found: {source}, page {page}"
    )


RBI_2017 = "RBI_Customer_Protection_2017.pdf"

RBI_2026 = "RBI_Integrated_Ombudsman_Scheme_2026.pdf"


# ============================================================
# 2. BASELINE INVESTIGATION
# ============================================================

def base_case():

    return {
        "dispute": (
            "Customer reports an unauthorized UPI transaction."
        ),

        "fraud_category": "UPI social engineering",

        "fraud_reason": (
            "Customer reported an unknown UPI transaction."
        ),

        "investigation_claims": [
            "The customer reported an unauthorized UPI transaction."
        ],

        "regulatory_evidence": [
            get_evidence(RBI_2017, 1),
            get_evidence(RBI_2026, 1)
        ]
    }


# ============================================================
# 3. EVALUATION SCENARIOS
# ============================================================

TEST_SCENARIOS = [

    # --------------------------------------------------------
    # EVIDENCE VALIDATION
    # --------------------------------------------------------

    {
        "id": 1,
        "name": "Valid historical evidence",
        "description": "Checks valid source and page references.",
        "input": base_case(),
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    {
        "id": 2,
        "name": "No regulatory evidence",
        "description": "Checks behaviour when evidence is missing.",
        "input": {
            **base_case(),
            "regulatory_evidence": []
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    {
        "id": 3,
        "name": "Empty evidence text",
        "description": "Checks evidence with empty text.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                {
                    "source": RBI_2017,
                    "page": 1,
                    "status": "historical",
                    "text": ""
                }
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    {
        "id": 4,
        "name": "Unknown document source",
        "description": "Checks a source absent from the local database.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                {
                    "source": "unknown_document.pdf",
                    "page": 1,
                    "status": "current",
                    "text": "Customer liability regulations."
                }
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    {
        "id": 5,
        "name": "Invalid page reference",
        "description": "Checks a page number absent from the source.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                {
                    "source": RBI_2017,
                    "page": 99999,
                    "status": "current",
                    "text": "Customer liability regulations."
                }
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    # --------------------------------------------------------
    # HISTORICAL AND REGULATORY EVIDENCE
    # --------------------------------------------------------

    {
        "id": 6,
        "name": "Historical transaction-liability evidence",
        "description": "Checks that historical evidence cannot establish current liability.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                get_evidence(RBI_2017, 1, "historical")
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    {
        "id": 7,
        "name": "Ombudsman evidence only",
        "description": "Checks that grievance-redressal evidence is not treated as transaction-liability evidence.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                get_evidence(RBI_2026, 1, "historical")
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    {
        "id": 8,
        "name": "Multiple historical documents",
        "description": "Checks that multiple historical sources do not automatically establish current liability.",
        "input": base_case(),
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    {
        "id": 9,
        "name": "Unclassified regulatory evidence",
        "description": "Checks evidence that does not match a known regulatory domain.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                {
                    "source": RBI_2026,
                    "page": 1,
                    "status": "historical",
                    "text": "A document containing unrelated administrative information."
                }
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE",
            "human_escalation": True
        }
    },

    # --------------------------------------------------------
    # CLAIM VERIFICATION
    # --------------------------------------------------------

    {
        "id": 10,
        "name": "Customer-reported factual claim",
        "description": "Checks whether a customer statement matches the complaint.",
        "input": base_case(),
        "expected": {
            "claim_statuses": [
                "CUSTOMER_REPORT_MATCH_REQUIRES_REVIEW"
            ]
        }
    },

    {
        "id": 11,
        "name": "Unsupported zero-liability claim",
        "description": "Checks whether an unsupported legal conclusion is rejected.",
        "input": {
            **base_case(),
            "investigation_claims": [
                "The customer has zero liability for the disputed transaction."
            ]
        },
        "expected": {
            "claim_statuses": [
                "NO_DIRECT_TEXT_MATCH_REQUIRES_HUMAN_REVIEW"
            ]
        }
    },

    {
        "id": 12,
        "name": "Mixed factual and legal claims",
        "description": "Checks whether factual and regulatory claims are treated differently.",
        "input": {
            **base_case(),
            "investigation_claims": [
                "The customer reported an unauthorized UPI transaction.",
                "The customer has zero liability for the disputed transaction."
            ]
        },
        "expected": {
            "claim_statuses": [
                "CUSTOMER_REPORT_MATCH_REQUIRES_REVIEW",
                "NO_DIRECT_TEXT_MATCH_REQUIRES_HUMAN_REVIEW"
            ]
        }
    },

    {
        "id": 13,
        "name": "Missing investigation claims",
        "description": "Checks behaviour when no claims are submitted.",
        "input": {
            **base_case(),
            "investigation_claims": []
        },
        "expected": {
            "human_escalation": True
        }
    },

    # --------------------------------------------------------
    # INVESTIGATION QUALITY
    # --------------------------------------------------------

    {
        "id": 14,
        "name": "Missing fraud category",
        "description": "Checks escalation when the fraud category is missing.",
        "input": {
            **base_case(),
            "fraud_category": ""
        },
        "expected": {
            "human_escalation": True
        }
    },

    {
        "id": 15,
        "name": "Uncertain fraud category",
        "description": "Checks escalation when manual review is required.",
        "input": {
            **base_case(),
            "fraud_category": "Needs manual review"
        },
        "expected": {
            "human_escalation": True
        }
    },

    {
        "id": 16,
        "name": "Missing fraud reasoning",
        "description": "Checks escalation when classification reasoning is absent.",
        "input": {
            **base_case(),
            "fraud_reason": ""
        },
        "expected": {
            "human_escalation": True
        }
    },

    # --------------------------------------------------------
    # DOMAIN AND LIABILITY GATING
    # --------------------------------------------------------

    {
        "id": 17,
        "name": "Grievance evidence cannot establish liability",
        "description": "Checks separation of grievance redressal and transaction liability.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                get_evidence(RBI_2026, 1, "current")
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE"
        }
    },

    {
        "id": 18,
        "name": "Withdrawn document falsely labelled current",
        "description": "Tests whether current-status metadata is trusted without checking the document's actual legal status.",
        "input": {
            **base_case(),
            "regulatory_evidence": [
                get_evidence(RBI_2017, 1, "current")
            ]
        },
        "expected": {
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE"
        },
        "known_limitation": True
    },

    # --------------------------------------------------------
    # ESCALATION AND RECOMMENDATION
    # --------------------------------------------------------

    {
        "id": 19,
        "name": "Unsupported claim triggers escalation",
        "description": "Checks that an unsupported legal claim leads to human review.",
        "input": {
            **base_case(),
            "investigation_claims": [
                "The bank must refund the customer immediately."
            ]
        },
        "expected": {
            "human_escalation": True,
            "verification_status": "ESCALATED"
        }
    },

    {
        "id": 20,
        "name": "Insufficient evidence triggers manual investigation",
        "description": "Checks the final recommendation when liability evidence is insufficient.",
        "input": {
            **base_case(),
            "regulatory_evidence": []
        },
        "expected": {
            "human_escalation": True,
            "verification_status": "ESCALATED",
            "liability_status": "INSUFFICIENT_VERIFIED_EVIDENCE"
        }
    }
]


# ============================================================
# 4. EXPECTATION CHECKER
# ============================================================

def check_expectations(result, expected):

    errors = []

    for key, expected_value in expected.items():

        if key == "claim_statuses":

            actual = [
                item.get("verification_status")
                for item in result.get("claim_verification", [])
            ]

        elif key == "has_consistency_issue":

            actual = bool(result.get("consistency_issues"))

        else:

            actual = result.get(key)

        if actual != expected_value:

            errors.append(
                f"{key}: expected {expected_value}, got {actual}"
            )

    return errors


# ============================================================
# 5. RUN ALL 20 SCENARIOS
# ============================================================

def run_evaluation():

    passed = 0
    failed = 0
    results = []

    print("\n==============================================")
    print(" DISPUTEAI VERIFICATION AGENT EVALUATION")
    print("==============================================")

    for scenario in TEST_SCENARIOS:

        print(
            f"\nTest {scenario['id']}: "
            f"{scenario['name']}"
        )

        try:

            test_input = copy.deepcopy(
                scenario["input"]
            )

            result = run_verification(test_input)

            errors = check_expectations(
                result,
                scenario["expected"]
            )

            if errors:

                status = "FAIL"
                failed += 1

                for error in errors:
                    print("  -", error)

            else:

                status = "PASS"
                passed += 1

            

            print("  Result:", status)
            print(
                "  Verification:",
                result.get("verification_status")
            )
            print(
                "  Liability:",
                result.get("liability_status")
            )
            print(
                "  Escalation:",
                result.get("human_escalation")
            )

            results.append({
                "id": scenario["id"],
                "name": scenario["name"],
                "status": status,
                "known_limitation": scenario.get(
                    "known_limitation", False
                ),
                "errors": errors,
                "verification_status": result.get(
                    "verification_status"
                ),
                "liability_status": result.get(
                    "liability_status"
                ),
                "human_escalation": result.get(
                    "human_escalation"
                )
            })

        except Exception as error:

            failed += 1

            print("  Result: ERROR")
            print("  Error:", str(error))

            results.append({
                "id": scenario["id"],
                "name": scenario["name"],
                "status": "ERROR",
                "error": str(error)
            })

    # ========================================================
    # 6. FINAL REPORT
    # ========================================================

    total = len(TEST_SCENARIOS)

    report = {
        "project": "DisputeAI",
        "module": "Verification Agent",
        "total_scenarios": total,
        "passed": passed,
        "failed": failed,
        "accuracy_percentage": round(
            (passed / total) * 100, 2
        ),
        "results": results
    }

    report_path = (
        ROOT / "evaluation"
        / "verification_agent_report.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )

    print("\n==============================================")
    print(" FINAL EVALUATION SUMMARY")
    print("==============================================")

    print("Total scenarios:", total)
    print("Passed:", passed)
    print("Failed:", failed)

    print(
        "Pass percentage:",
        report["accuracy_percentage"], "%"
    )

    print("\nReport saved to:")
    print(report_path)

    print("\n==============================================")


if __name__ == "__main__":

    run_evaluation()