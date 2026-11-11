
from src.fraud_classifier import classify_fraud
from src.regulatory_tools import search_regulations


def fraud_investigation_agent(state):
    """Agent 1: Classifies the customer's dispute."""

    result = classify_fraud(state["dispute"])

    return {
        "fraud_category": result["category"],
        "fraud_reason": result["reason"]
    }


def regulatory_compliance_agent(state):
    """Agent 2: Retrieves regulatory evidence."""

    question = (
        state["dispute"]
        + " "
        + state["fraud_category"]
    )

    evidence = search_regulations(question, top_k=5)

    return {
        "regulatory_evidence": evidence
    }


print("Both investigation agents created successfully!")
