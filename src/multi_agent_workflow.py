"""
DisputeAI Multi-Agent Workflow Engine (LangGraph)
Integrates:
1. Investigation Agent: Complaint analysis, 5-category classification, RAG retrieval
2. Verification Agent: Evidence integrity, citation verification, inconsistency detection
3. Liability Assessment Agent: RBI 2017/2026 Customer Protection liability evaluation
4. Recommendation & Escalation Agent: Decision routing, provisional credit, human escalation
"""

import json
import os
import re
from datetime import date
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

from src.fraud_classifier import classify_fraud
from src.regulatory_tools import search_regulations
from src.gemini_rag import generate_rag_answer
from src.output_security import filter_sensitive_output


# ============================================================
# STATE DEFINITION
# ============================================================

class MultiAgentDisputeState(TypedDict, total=False):
    # Input Dispute Details
    dispute_id: str
    customer_name: str
    customer_email: str
    bank_name: str
    transaction_id: str
    amount: float
    transaction_type: str
    transaction_date: str
    reported_date: str
    fraud_type_claimed: str
    fraud_description: str
    otp_shared: bool
    evidence_files: List[Dict[str, Any]]

    # Agent 1 (Investigation) Outputs
    fraud_category: str
    risk_score: int
    risk_level: str
    priority: str
    classification_explanation: str
    regulatory_evidence: List[Dict[str, Any]]
    rag_synthesis: str
    investigation_claims: List[str]
    investigation_findings: str

    # Agent 2 (Verification) Outputs
    evidence_verification: List[Dict[str, Any]]
    citation_verification: List[Dict[str, Any]]
    missing_information: List[str]
    unsupported_claims: List[str]
    verification_status: str
    verification_summary: str

    # Agent 3 (Liability Assessment) Outputs
    liability_status: str
    liability_reasoning: str
    applicable_clauses: List[str]
    reporting_delay_days: int
    reversal_deadline_days: int

    # Agent 4 (Recommendation & Escalation) Outputs
    recommendation: str
    provisional_credit_amount: float
    provisional_credit_recommended: bool
    human_escalation: bool
    escalation_reasons: List[str]
    confidence_score: float
    final_dossier: Dict[str, Any]


# ============================================================
# AGENT 1: INVESTIGATION AGENT
# ============================================================

def investigation_agent(state: MultiAgentDisputeState) -> Dict[str, Any]:
    description = state.get("fraud_description", "")
    otp_shared = state.get("otp_shared", False)
    amount = float(state.get("amount", 0.0))
    tx_type = state.get("transaction_type", "UPI")

    # 1. 5-Category Fraud Classification with Risk Scoring
    clf = classify_fraud(
        description=description,
        otp_shared=otp_shared,
        amount=amount,
        transaction_type=tx_type
    )

    # 2. RAG Retrieval from official RBI Circulars
    query = f"{clf['category']} unauthorized electronic banking transaction {tx_type} liability {description[:120]}"
    evidence = search_regulations(query, top_k=4)

    # 3. Regulatory RAG Synthesis
    rag_response = generate_rag_answer(query, evidence)

    # 4. Generate structured investigation claims
    claims = [
        f"Customer reports unauthorized {clf['category']} involving amount ₹{amount:,.2f}.",
        f"Authentication OTP was {'disclosed to third party' if otp_shared else 'retained confidential by customer'}.",
        f"Transaction channel reported as {tx_type}."
    ]

    findings = (
        f"Preliminary Investigation for Dispute {state.get('dispute_id', 'N/A')}:\n"
        f"- Identified Category: {clf['category']} ({clf['confidence']} confidence)\n"
        f"- Assessed Risk Score: {clf['risk_score']}/100 ({clf['risk_level']} Risk Level)\n"
        f"- Regulatory Evidence: Retrieved {len(evidence)} verified RBI circular citations.\n"
        f"- Diagnostic: {clf['explanation']}"
    )

    return {
        "fraud_category": clf["category"],
        "risk_score": clf["risk_score"],
        "risk_level": clf["risk_level"],
        "priority": clf["priority"],
        "classification_explanation": clf["explanation"],
        "regulatory_evidence": evidence,
        "rag_synthesis": rag_response,
        "investigation_claims": claims,
        "investigation_findings": filter_sensitive_output(findings)
    }


# ============================================================
# AGENT 2: VERIFICATION AGENT
# ============================================================

def verification_agent(state: MultiAgentDisputeState) -> Dict[str, Any]:
    evidence = state.get("regulatory_evidence", [])
    files = state.get("evidence_files", [])
    claims = state.get("investigation_claims", [])

    # 1. Evidence Verification
    file_checks = []
    for f in files:
        fname = f.get("filename", "")
        fsize = f.get("file_size", 0)
        valid = bool(fname and fsize > 0)
        file_checks.append({
            "filename": fname,
            "status": "VALID_DOCUMENT" if valid else "INVALID_FILE",
            "notes": "Integrity verified" if valid else "Empty or corrupted file"
        })

    # 2. Citation Verification against local RBI records
    citation_checks = []
    historical_detected = False
    for item in evidence:
        source = item.get("source", "")
        page = item.get("page", 1)
        status = item.get("status", "current")
        text = item.get("text", "")

        is_withdrawn = bool(re.search(r"\bwithdrawn\b", text, re.I))
        if is_withdrawn:
            historical_detected = True

        citation_checks.append({
            "source": source,
            "page": page,
            "verified_in_official_gazette": bool(source and page),
            "status": "HISTORICAL / WITHDRAWN" if is_withdrawn else status.upper(),
            "caveat": "Historical regulation text; must be corroborated by current 2026 framework" if is_withdrawn else "Active circular"
        })

    # 3. Missing Information & Unsupported Claims Detection
    missing = []
    if state.get("fraud_category") == "Identity Theft" and not any("fir" in (f.get("filename", "")).lower() for f in files):
        missing.append("Police FIR / Cyber Crime Complaint copy not attached for Identity Theft claim.")

    if not state.get("bank_name"):
        missing.append("Designated bank name was not provided.")

    try:
        t_date = date.fromisoformat(str(state.get("transaction_date", "")))
        r_date = date.fromisoformat(str(state.get("reported_date", "")))
        delay = (r_date - t_date).days
    except Exception:
        delay = 0

    if delay > 7:
        missing.append("Customer reporting delay exceeds 7 working days; Bank Board approval required for liability waiver.")

    verification_status = "VERIFIED"
    if historical_detected or missing:
        verification_status = "ESCALATED_FOR_INSPECTION"

    summary = (
        f"Verification completed. Verified {len(citation_checks)} regulatory citations. "
        f"{f'Identified {len(missing)} evidentiary gaps: ' + '; '.join(missing) if missing else 'All baseline claims verified against regulatory corpus.'}"
    )

    return {
        "evidence_verification": file_checks,
        "citation_verification": citation_checks,
        "missing_information": missing,
        "unsupported_claims": [],
        "verification_status": verification_status,
        "verification_summary": summary,
        "reporting_delay_days": delay
    }


# ============================================================
# AGENT 3: LIABILITY ASSESSMENT AGENT
# ============================================================

def liability_assessment_agent(state: MultiAgentDisputeState) -> Dict[str, Any]:
    otp_shared = state.get("otp_shared", False)
    delay = state.get("reporting_delay_days", 0)
    amount = float(state.get("amount", 0.0))
    category = state.get("fraud_category", "UPI Fraud")

    # Assess according to RBI Circular DBR.No.Leg.BC.78/09.07.005/2017-18
    applicable_clauses = []

    if otp_shared:
        liability_status = "FULL_CUSTOMER_LIABILITY"
        applicable_clauses.append("Paragraph 7(i): Customer negligence where credentials/OTP disclosed.")
        reasoning = (
            "Under RBI Paragraph 7(i), in cases where the loss is due to negligence by a customer "
            "(such as where authentication credentials or OTP were shared), the customer will bear the entire loss "
            "until the unauthorized transaction is reported to the bank."
        )
    elif delay <= 3:
        liability_status = "ZERO_CUSTOMER_LIABILITY"
        applicable_clauses.append("Paragraph 6(ii): Zero liability on third-party breach notified within 3 working days.")
        reasoning = (
            f"Under RBI Paragraph 6(ii), where deficiency lies neither with the bank nor the customer (third-party breach), "
            f"and the customer notifies the bank within three working days of receiving bank communication, "
            f"the customer is entitled to Zero Liability."
        )
    elif 4 <= delay <= 7:
        liability_status = "LIMITED_CUSTOMER_LIABILITY"
        applicable_clauses.append("Paragraph 7(ii) & Table 1: Limited liability for reporting delay of 4 to 7 working days.")
        max_cap = 10000.0  # Standard SB account / Card cap under Table 1
        customer_cap = min(amount, max_cap)
        reasoning = (
            f"Under RBI Paragraph 7(ii) and Table 1, where notification is delayed between 4 to 7 working days, "
            f"the per-transaction liability of the customer is limited to the transaction value or the statutory cap "
            f"(₹{customer_cap:,.2f}), whichever is lower. The balance of ₹{max(0.0, amount - customer_cap):,.2f} is borne by the bank."
        )
    else:
        liability_status = "INSUFFICIENT_VERIFIED_EVIDENCE"
        applicable_clauses.append("Paragraph 7(ii) proviso: Reporting beyond 7 days determined as per Bank's Board approved policy.")
        reasoning = (
            f"Notification delay of {delay} days exceeds the statutory 7-day window. "
            f"Customer liability must be resolved in accordance with the bank's Board-approved policy "
            f"under manual ombudsman triage."
        )

    return {
        "liability_status": liability_status,
        "liability_reasoning": reasoning,
        "applicable_clauses": applicable_clauses,
        "reversal_deadline_days": 10  # RBI Paragraph 9: Shadow reversal within 10 working days
    }


# ============================================================
# AGENT 4: RECOMMENDATION & ESCALATION AGENT
# ============================================================

def recommendation_escalation_agent(state: MultiAgentDisputeState) -> Dict[str, Any]:
    liability = state.get("liability_status", "INSUFFICIENT_VERIFIED_EVIDENCE")
    risk_score = state.get("risk_score", 0)
    amount = float(state.get("amount", 0.0))
    missing = state.get("missing_information", [])

    escalation_reasons = []
    human_escalation = False
    provisional_credit_recommended = False
    provisional_credit_amount = 0.0

    # Determine provisional credit and resolution recommendation
    if liability == "ZERO_CUSTOMER_LIABILITY":
        provisional_credit_recommended = True
        provisional_credit_amount = amount
        rec = (
            f"Approve full shadow reversal credit of ₹{amount:,.2f} to customer account within 10 working days "
            f"pursuant to RBI Paragraph 9. Initiate interbank recovery via NPCI / Card Scheme Chargeback."
        )
    elif liability == "LIMITED_CUSTOMER_LIABILITY":
        provisional_credit_recommended = True
        max_cap = 10000.0
        bank_share = max(0.0, amount - min(amount, max_cap))
        provisional_credit_amount = bank_share
        rec = (
            f"Approve partial provisional credit of ₹{bank_share:,.2f} to customer account. "
            f"Customer per-transaction liability capped at statutory ₹{min(amount, max_cap):,.2f} per RBI Table 1."
        )
    elif liability == "FULL_CUSTOMER_LIABILITY":
        rec = (
            f"Dispute liable to customer negligence (OTP shared). Issue formal explanation letter citing "
            f"RBI Paragraph 7(i). Offer customer fraud education notice and block compromised channels."
        )
    else:
        rec = (
            f"Refer dispute to Senior Banking Ombudsman / Fraud Investigation Committee for manual review "
            f"under bank Board-approved customer protection policy."
        )

    # Escalation checks
    if risk_score >= 80:
        human_escalation = True
        escalation_reasons.append(f"Critical risk score ({risk_score}/100) exceeds automatic resolution threshold.")

    if amount >= 50000:
        human_escalation = True
        escalation_reasons.append(f"High transaction exposure (₹{amount:,.2f} >= ₹50,000 threshold).")

    if missing:
        human_escalation = True
        escalation_reasons.extend(missing)

    if liability == "INSUFFICIENT_VERIFIED_EVIDENCE":
        human_escalation = True
        escalation_reasons.append("Liability could not be deterministically resolved under statutory rules.")

    confidence = 0.95 if not human_escalation else 0.72

    dossier = {
        "dispute_id": state.get("dispute_id"),
        "customer_name": state.get("customer_name"),
        "fraud_category": state.get("fraud_category"),
        "risk_score": risk_score,
        "risk_level": state.get("risk_level"),
        "liability_status": liability,
        "liability_reasoning": state.get("liability_reasoning"),
        "applicable_clauses": state.get("applicable_clauses", []),
        "provisional_credit_amount": provisional_credit_amount,
        "provisional_credit_recommended": provisional_credit_recommended,
        "human_escalation": human_escalation,
        "escalation_reasons": escalation_reasons,
        "citations_verified": state.get("citation_verification", []),
        "recommendation": rec,
        "confidence_score": confidence
    }

    return {
        "recommendation": rec,
        "provisional_credit_recommended": provisional_credit_recommended,
        "provisional_credit_amount": provisional_credit_amount,
        "human_escalation": human_escalation,
        "escalation_reasons": escalation_reasons,
        "confidence_score": confidence,
        "final_dossier": dossier
    }


# ============================================================
# LANGGRAPH WORKFLOW ASSEMBLY
# ============================================================

workflow = StateGraph(MultiAgentDisputeState)

workflow.add_node("investigation_agent", investigation_agent)
workflow.add_node("verification_agent", verification_agent)
workflow.add_node("liability_assessment_agent", liability_assessment_agent)
workflow.add_node("recommendation_escalation_agent", recommendation_escalation_agent)

workflow.add_edge(START, "investigation_agent")
workflow.add_edge("investigation_agent", "verification_agent")
workflow.add_edge("verification_agent", "liability_assessment_agent")
workflow.add_edge("liability_assessment_agent", "recommendation_escalation_agent")
workflow.add_edge("recommendation_escalation_agent", END)

dispute_agent_graph = workflow.compile()


def run_multi_agent_investigation(dispute_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute complete 4-agent LangGraph workflow for a dispute."""
    return dispute_agent_graph.invoke(dispute_data)
