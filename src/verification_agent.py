
import json
import os
import re
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ============================================================
# 1. VERIFICATION STATE
# ============================================================

class VerificationState(TypedDict, total=False):
    dispute: str
    fraud_category: str
    fraud_reason: str

    regulatory_evidence: list[dict]
    regulatory_domain_checks: list[dict]
    regulatory_status_checks: list[dict]
    investigation_claims: list[str]

    evidence_checks: list[dict]
    authenticity_checks: list[dict]
    citation_checks: list[dict]
    claim_verification: list[dict]
    consistency_issues: list[str]

    liability_status: str
    verification_status: str
    recommendation: str
    human_escalation: bool
    verification_summary: str


# ============================================================
# 2. LOAD RBI EVIDENCE DATABASE
# ============================================================

def load_rbi_records():

    database_path = os.path.join(
        "documents",
        "processed",
        "rbi_chunks.json"
    )

    if not os.path.exists(database_path):
        raise FileNotFoundError(
            f"RBI evidence database not found: {database_path}"
        )

    with open(database_path, "r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError(
            "RBI evidence database must contain a list."
        )

    return records


# ============================================================
# 3. DOCUMENT REFERENCE VERIFICATION
# ============================================================

def verify_document_authenticity(evidence):

    try:
        records = load_rbi_records()

    except (
        FileNotFoundError,
        ValueError,
        OSError,
        json.JSONDecodeError
    ) as error:

        return [
            {
                "source": item.get("source"),
                "page": item.get("page"),
                "document_exists": False,
                "authenticity_status": "DATABASE_ERROR",
                "reason": str(error)
            }
            for item in evidence
            if isinstance(item, dict)
        ]

    verified_records = {
        (
            record.get("source"),
            record.get("page_number")
        )
        for record in records
        if isinstance(record, dict)
    }

    results = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        source = item.get("source")
        page = item.get("page")

        exists = (source, page) in verified_records

        results.append({
            "source": source,
            "page": page,
            "document_exists": exists,
            "authenticity_status": (
                "VERIFIED" if exists else "NOT_FOUND"
            ),
            "reason": (
                "Document source and page exist in the local RBI evidence database."
                if exists
                else "Document source and page were not found in the local RBI evidence database."
            )
        })

    return results


# ============================================================
# 4. REGULATORY STATUS VALIDATION
# ============================================================

def detect_regulatory_status(text):
    """
    Detect a withdrawal stamp at the very end of an extracted page.

    This is a conservative text heuristic, not an authoritative legal
    status lookup. A trailing "Withdrawn" marker is treated as a warning
    that the evidence must not support a current-liability conclusion.
    """
    normalized = str(text or "").strip()

    trailing_withdrawal_marker = re.search(
        r"\bwithdrawn\s*[.)\]]*\s*$",
        normalized,
        flags=re.IGNORECASE
    )

    if trailing_withdrawal_marker:
        return {
            "detected_status": "WITHDRAWN",
            "status_marker_detected": True,
            "reason": (
                "The extracted evidence ends with a 'Withdrawn' marker. "
                "It must not be treated as current regulatory authority "
                "without independent official-source verification."
            )
        }

    return {
        "detected_status": "NOT_DETECTED",
        "status_marker_detected": False,
        "reason": (
            "No recognized trailing withdrawal marker was detected. "
            "This does not independently establish that the document is current."
        )
    }


def validate_regulatory_status(evidence):
    results = []

    for item in evidence:
        if not isinstance(item, dict):
            continue

        source = item.get("source")
        page = item.get("page")
        declared_status = str(item.get("status", "")).strip().lower()
        detected = detect_regulatory_status(item.get("text", ""))

        status_conflict = (
            declared_status == "current"
            and detected["detected_status"] == "WITHDRAWN"
        )

        results.append({
            "source": source,
            "page": page,
            "declared_status": declared_status or "UNSPECIFIED",
            "detected_status": detected["detected_status"],
            "status_marker_detected": detected["status_marker_detected"],
            "status_conflict": status_conflict,
            "status_valid_for_current_use": (
                declared_status == "current"
                and not detected["status_marker_detected"]
            ),
            "reason": (
                "STATUS CONFLICT: evidence is labelled current but contains "
                "a trailing withdrawal marker."
                if status_conflict
                else detected["reason"]
            )
        })

    return results


# ============================================================
# 4. EVIDENCE COMPLETENESS VERIFICATION
# ============================================================

def verify_evidence(state):

    evidence = state.get("regulatory_evidence", [])
    checks = []

    for item in evidence:

        if not isinstance(item, dict):

            checks.append({
                "source": None,
                "page": None,
                "valid": False,
                "reason": "Evidence item is not a valid dictionary."
            })

            continue

        has_text = bool(str(item.get("text", "")).strip())
        has_source = bool(str(item.get("source", "")).strip())

        page = item.get("page")

        has_page = (
            isinstance(page, int)
            and not isinstance(page, bool)
            and page > 0
        )

        valid = has_text and has_source and has_page

        checks.append({
            "source": item.get("source"),
            "page": page,
            "valid": valid,
            "reason": (
                "Evidence contains text, source and page reference."
                if valid
                else "Evidence is missing valid text, source or page reference."
            )
        })

    authenticity_checks = verify_document_authenticity(evidence)
    regulatory_status_checks = validate_regulatory_status(evidence)

    return {
        "evidence_checks": checks,
        "authenticity_checks": authenticity_checks,
        "regulatory_status_checks": regulatory_status_checks
    }


# ============================================================
# 5. CITATION VERIFICATION
# ============================================================

def verify_citations(state):

    evidence = state.get("regulatory_evidence", [])

    try:
        records = load_rbi_records()

    except (
        FileNotFoundError,
        ValueError,
        OSError,
        json.JSONDecodeError
    ) as error:

        return {
            "citation_checks": [
                {
                    "source": item.get("source"),
                    "page": item.get("page"),
                    "citation_valid": False,
                    "reason": f"Evidence database unavailable: {error}"
                }
                for item in evidence
                if isinstance(item, dict)
            ]
        }

    valid_references = {
        (
            record.get("source"),
            record.get("page_number")
        )
        for record in records
        if isinstance(record, dict)
    }

    checks = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        source = item.get("source")
        page = item.get("page")

        valid_format = (
            isinstance(source, str)
            and bool(source.strip())
            and isinstance(page, int)
            and not isinstance(page, bool)
            and page > 0
        )

        reference_exists = (
            valid_format
            and (source, page) in valid_references
        )

        checks.append({
            "source": source,
            "page": page,
            "citation_valid": bool(reference_exists),
            "reason": (
                "Citation format is valid and the source/page exists in the local RBI evidence database."
                if reference_exists
                else (
                    "Citation format is invalid."
                    if not valid_format
                    else "The cited source/page does not exist in the local RBI evidence database."
                )
            )
        })

    return {
        "citation_checks": checks
    }


# ============================================================
# 6. REGULATORY DOMAIN CLASSIFICATION
# ============================================================

def classify_regulatory_domains(state):

    evidence = state.get("regulatory_evidence", [])
    citation_checks = state.get("citation_checks", [])
    authenticity_checks = state.get("authenticity_checks", [])
    regulatory_status_checks = state.get("regulatory_status_checks", [])

    results = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        source = item.get("source")
        page = item.get("page")

        citation_verified = any(
            check.get("source") == source
            and check.get("page") == page
            and check.get("citation_valid") is True
            for check in citation_checks
            if isinstance(check, dict)
        )

        document_verified = any(
            check.get("source") == source
            and check.get("page") == page
            and check.get("authenticity_status") == "VERIFIED"
            for check in authenticity_checks
            if isinstance(check, dict)
        )

        if not citation_verified or not document_verified:

            results.append({
                "source": source,
                "page": page,
                "regulatory_domain": "UNVERIFIED_EVIDENCE",
                "classification_reason": (
                    "Evidence was not classified because its citation "
                    "or document reference failed verification."
                )
            })

            continue

        status_check = next(
            (
                check for check in regulatory_status_checks
                if isinstance(check, dict)
                and check.get("source") == source
                and check.get("page") == page
            ),
            {}
        )

        if status_check.get("detected_status") == "WITHDRAWN":
            results.append({
                "source": source,
                "page": page,
                "regulatory_domain": "WITHDRAWN_EVIDENCE",
                "classification_reason": (
                    "A trailing withdrawal marker was detected. "
                    "This evidence is excluded from current liability support."
                )
            })
            continue

        source_text = str(source or "").lower()
        evidence_text = str(item.get("text", "")).lower()

        combined_text = (
            source_text + " " + evidence_text
        ).replace("_", " ").replace("-", " ")

        domain = "OTHER_OR_UNCLASSIFIED"
        reason = "No clear regulatory domain identified."

        if (
            "customer protection" in combined_text
            or "limiting liability" in combined_text
            or "unauthorised electronic banking transactions" in combined_text
            or "unauthorized electronic banking transactions" in combined_text
            or "customer liability" in combined_text
        ):

            domain = "TRANSACTION_LIABILITY"

            reason = (
                "Evidence concerns customer protection "
                "or liability for unauthorised transactions."
            )

        elif (
            "integrated ombudsman scheme" in combined_text
            or "ombudsman" in combined_text
            or "complaint redressal" in combined_text
            or "grievance redressal" in combined_text
        ):

            domain = "GRIEVANCE_REDRESSAL"

            reason = (
                "Evidence concerns complaint handling "
                "and regulatory grievance redressal."
            )

        results.append({
            "source": source,
            "page": page,
            "regulatory_domain": domain,
            "classification_reason": reason
        })

    return {
        "regulatory_domain_checks": results
    }


# ============================================================
# 7. CLAIM CLASSIFICATION HELPERS
# ============================================================

def normalize_text(text):

    text = str(text or "").lower()

    text = re.sub(r"[^a-z0-9\s]", " ", text)

    return " ".join(text.split())


def get_claim_type(claim):

    normalized_claim = normalize_text(claim)

    regulatory_keywords = [
        "liability",
        "liable",
        "zero liability",
        "customer protection",
        "rbi",
        "regulation",
        "regulatory",
        "ombudsman",
        "circular",
        "guideline",
        "compensation",
        "reimbursement",
        "bank is responsible",
        "bank must",
        "bank should",
        "legal obligation",
        "legally responsible",
        "unauthorised transaction",
        "unauthorized transaction"
    ]

    if any(
        keyword in normalized_claim
        for keyword in regulatory_keywords
    ):
        return "REGULATORY_OR_LEGAL"

    return "CUSTOMER_REPORTED_FACT"


def compare_customer_claim_with_dispute(claim, dispute):

    claim_words = set(normalize_text(claim).split())
    dispute_words = set(normalize_text(dispute).split())

    if not claim_words or not dispute_words:
        return False, 0.0

    overlap = claim_words.intersection(dispute_words)

    score = len(overlap) / len(claim_words)

    # This only checks consistency with the complaint,
    # not whether the customer's statement is factually true.
    matched = score >= 0.65

    return matched, round(score, 2)


# ============================================================
# 8. CLAIM-TO-EVIDENCE VERIFICATION
# ============================================================

def verify_claims_against_evidence(state):

    claims = state.get("investigation_claims", [])
    evidence = state.get("regulatory_evidence", [])
    dispute = state.get("dispute", "")

    try:
        records = load_rbi_records()

    except (
        FileNotFoundError,
        ValueError,
        OSError,
        json.JSONDecodeError
    ) as error:

        return {
            "claim_verification": [
                {
                    "claim": claim,
                    "claim_type": "UNKNOWN",
                    "matched_terms": [],
                    "matching_score": 0.0,
                    "matched_sources": [],
                    "verification_status": "REQUIRES_HUMAN_REVIEW",
                    "reason": f"Evidence database unavailable: {error}"
                }
                for claim in claims
            ]
        }

    citation_checks = state.get("citation_checks", [])
    authenticity_checks = state.get("authenticity_checks", [])

    results = []

    for claim in claims:

        claim_type = get_claim_type(claim)

        matched_sources = []
        matched_terms = []
        matching_score = 0.0

        # ----------------------------------------------------
        # A. CUSTOMER-REPORTED FACTUAL CLAIM
        # ----------------------------------------------------

        if claim_type == "CUSTOMER_REPORTED_FACT":

            matched, score = compare_customer_claim_with_dispute(
                claim,
                dispute
            )

            matching_score = score

            if matched:

                status = "CUSTOMER_REPORT_MATCH_REQUIRES_REVIEW"

                reason = (
                    "The claim is consistent with information in the "
                    "customer's complaint. This does not independently "
                    "prove that the reported event occurred."
                )

            else:

                status = "NOT_VERIFIABLE_FROM_AVAILABLE_INPUTS"

                reason = (
                    "The claim could not be sufficiently matched against "
                    "the original complaint. Additional information or "
                    "human review is required."
                )

        # ----------------------------------------------------
        # B. REGULATORY OR LEGAL CLAIM
        # ----------------------------------------------------

        else:

            claim_normalized = normalize_text(claim)

            exact_match_found = False

            for item in evidence:

                if not isinstance(item, dict):
                    continue

                source = item.get("source")
                page = item.get("page")

                citation_verified = any(
                    check.get("source") == source
                    and check.get("page") == page
                    and check.get("citation_valid") is True
                    for check in citation_checks
                    if isinstance(check, dict)
                )

                authenticity_verified = any(
                    check.get("source") == source
                    and check.get("page") == page
                    and check.get("authenticity_status") == "VERIFIED"
                    for check in authenticity_checks
                    if isinstance(check, dict)
                )

                # Only inspect evidence with verified references.
                if not citation_verified or not authenticity_verified:
                    continue

                matching_records = [
                    record
                    for record in records
                    if (
                        record.get("source") == source
                        and record.get("page_number") == page
                    )
                ]

                for record in matching_records:

                    source_text = normalize_text(
                        record.get("text", "")
                    )

                    if (
                        claim_normalized
                        and claim_normalized in source_text
                    ):

                        exact_match_found = True

                        matched_sources.append({
                            "source": source,
                            "page": page
                        })

            if exact_match_found:

                status = "DIRECT_TEXT_MATCH_REQUIRES_HUMAN_REVIEW"

                reason = (
                    "The claim text appears in a verified cited document. "
                    "Context, applicability, current validity and legal "
                    "meaning still require human verification."
                )

            else:

                status = "NO_DIRECT_TEXT_MATCH_REQUIRES_HUMAN_REVIEW"

                reason = (
                    "The claim was not found as an exact text match "
                    "in the verified cited evidence. Keyword overlap "
                    "is not treated as proof of regulatory support."
                )

        results.append({
            "claim": claim,
            "claim_type": claim_type,
            "matched_terms": matched_terms,
            "matching_score": matching_score,
            "matched_sources": matched_sources,
            "verification_status": status,
            "reason": reason
        })

    return {
        "claim_verification": results
    }


# ============================================================
# 9. CONSISTENCY CHECK
# ============================================================

def check_consistency(state):

    issues = []

    category = state.get("fraud_category", "")

    if (
        not category
        or category == "Needs manual review"
    ):

        issues.append(
            "Fraud category is uncertain."
        )

    if not state.get("fraud_reason"):

        issues.append(
            "Fraud classification reasoning is missing."
        )

    evidence = state.get("regulatory_evidence", [])
    regulatory_status_checks = state.get("regulatory_status_checks", [])

    if any(
        isinstance(check, dict) and check.get("status_conflict") is True
        for check in regulatory_status_checks
    ):
        issues.append(
            "Regulatory status conflict: evidence is labelled current but contains a withdrawal marker."
        )

    if not evidence:

        issues.append(
            "No regulatory evidence was retrieved."
        )

    if evidence and not any(
        isinstance(item, dict)
        and item.get("status") == "current"
        for item in evidence
    ):

        issues.append(
            "No evidence explicitly marked as current was retrieved."
        )

    if any(
        not isinstance(item, dict)
        or not str(item.get("text", "")).strip()
        for item in evidence
    ):

        issues.append(
            "One or more evidence chunks are empty or invalid."
        )

    authenticity_checks = state.get(
        "authenticity_checks", []
    )

    if (
        not authenticity_checks
        or any(
            item.get("authenticity_status") != "VERIFIED"
            for item in authenticity_checks
            if isinstance(item, dict)
        )
        or any(
            not isinstance(item, dict)
            for item in authenticity_checks
        )
    ):

        issues.append(
            "One or more cited document/page references could not be verified."
        )

    domain_checks = state.get(
        "regulatory_domain_checks", []
    )

    if not domain_checks:

        issues.append(
            "Regulatory domain classification is missing."
        )

    if any(
        item.get("regulatory_domain") in [
            "OTHER_OR_UNCLASSIFIED",
            "UNVERIFIED_EVIDENCE"
        ]
        for item in domain_checks
        if isinstance(item, dict)
    ):

        issues.append(
            "One or more regulatory evidence items are unclassified or unverified."
        )

    claim_results = state.get(
        "claim_verification", []
    )

    if not claim_results:

        issues.append(
            "Investigation claims were not verified."
        )

    acceptable_claim_statuses = {
        "DIRECT_TEXT_MATCH_REQUIRES_HUMAN_REVIEW",
        "CUSTOMER_REPORT_MATCH_REQUIRES_REVIEW"
    }

    if any(
        item.get("verification_status") not in acceptable_claim_statuses
        for item in claim_results
        if isinstance(item, dict)
    ):

        issues.append(
            "One or more claims could not be matched to the available evidence or complaint."
        )

    if claim_results:

        issues.append(
            "Claim meaning and regulatory applicability require human review."
        )

    return {
        "consistency_issues": issues
    }


# ============================================================
# 10. LIABILITY ASSESSMENT
# ============================================================

def assess_liability(state):

    evidence = state.get("regulatory_evidence", [])
    domain_checks = state.get("regulatory_domain_checks", [])
    authenticity_checks = state.get("authenticity_checks", [])
    citation_checks = state.get("citation_checks", [])
    regulatory_status_checks = state.get("regulatory_status_checks", [])

    valid_current_liability_evidence = [
        item
        for item in evidence
        if (
            isinstance(item, dict)
            and item.get("status") == "current"
            and not any(
                check.get("source") == item.get("source")
                and check.get("page") == item.get("page")
                and check.get("detected_status") == "WITHDRAWN"
                for check in regulatory_status_checks
                if isinstance(check, dict)
            )
            and str(item.get("text", "")).strip()
            and str(item.get("source", "")).strip()
            and isinstance(item.get("page"), int)
            and not isinstance(item.get("page"), bool)
            and item.get("page") > 0
            and any(
                check.get("source") == item.get("source")
                and check.get("page") == item.get("page")
                and check.get("regulatory_domain")
                == "TRANSACTION_LIABILITY"
                for check in domain_checks
                if isinstance(check, dict)
            )
            and any(
                check.get("source") == item.get("source")
                and check.get("page") == item.get("page")
                and check.get("citation_valid") is True
                for check in citation_checks
                if isinstance(check, dict)
            )
        )
    ]

    verified_liability_evidence = [
        item
        for item in valid_current_liability_evidence
        if any(
            check.get("source") == item.get("source")
            and check.get("page") == item.get("page")
            and check.get("authenticity_status") == "VERIFIED"
            for check in authenticity_checks
            if isinstance(check, dict)
        )
    ]

    if not verified_liability_evidence:

        status = "INSUFFICIENT_VERIFIED_EVIDENCE"

    else:

        status = "REQUIRES_HUMAN_LEGAL_REVIEW"

    return {
        "liability_status": status
    }


# ============================================================
# 11. RECOMMENDATION ROUTING
# ============================================================

def route_recommendation(state):

    issues = state.get("consistency_issues", [])
    evidence_checks = state.get("evidence_checks", [])
    citation_checks = state.get("citation_checks", [])
    authenticity_checks = state.get("authenticity_checks", [])
    claim_results = state.get("claim_verification", [])

    invalid_evidence = (
        not evidence_checks
        or any(
            not item.get("valid", False)
            for item in evidence_checks
            if isinstance(item, dict)
        )
        or any(
            not isinstance(item, dict)
            for item in evidence_checks
        )
    )

    invalid_citations = (
        not citation_checks
        or any(
            not item.get("citation_valid", False)
            for item in citation_checks
            if isinstance(item, dict)
        )
        or any(
            not isinstance(item, dict)
            for item in citation_checks
        )
    )

    invalid_authenticity = (
        not authenticity_checks
        or any(
            item.get("authenticity_status") != "VERIFIED"
            for item in authenticity_checks
            if isinstance(item, dict)
        )
        or any(
            not isinstance(item, dict)
            for item in authenticity_checks
        )
    )

    acceptable_claim_statuses = {
        "DIRECT_TEXT_MATCH_REQUIRES_HUMAN_REVIEW",
        "CUSTOMER_REPORT_MATCH_REQUIRES_REVIEW"
    }

    unsupported_claims = (
        not claim_results
        or any(
            item.get("verification_status") not in acceptable_claim_statuses
            for item in claim_results
            if isinstance(item, dict)
        )
        or any(
            not isinstance(item, dict)
            for item in claim_results
        )
    )

    escalate = (
        bool(issues)
        or invalid_evidence
        or invalid_citations
        or invalid_authenticity
        or unsupported_claims
        or any(
            isinstance(check, dict) and check.get("status_conflict") is True
            for check in state.get("regulatory_status_checks", [])
        )
        or state.get("liability_status")
        != "REQUIRES_HUMAN_LEGAL_REVIEW"
    )

    if escalate:

        recommendation = (
            "Send the dispute for human investigation "
            "and manual regulatory verification."
        )

        status = "ESCALATED"

    else:

        recommendation = (
            "Preliminary evidence checks passed. "
            "Human legal review is still required before "
            "any final liability decision."
        )

        status = "VERIFICATION_PASSED"

    return {
        "human_escalation": escalate,
        "recommendation": recommendation,
        "verification_status": status
    }


# ============================================================
# 12. BUILD LANGGRAPH WORKFLOW
# ============================================================

workflow = StateGraph(VerificationState)

workflow.add_node(
    "evidence_verification",
    verify_evidence
)

workflow.add_node(
    "citation_verification",
    verify_citations
)

workflow.add_node(
    "regulatory_domain_classification",
    classify_regulatory_domains
)

workflow.add_node(
    "claim_verification",
    verify_claims_against_evidence
)

workflow.add_node(
    "consistency_check",
    check_consistency
)

workflow.add_node(
    "liability_assessment",
    assess_liability
)

workflow.add_node(
    "recommendation_routing",
    route_recommendation
)

workflow.add_edge(
    START,
    "evidence_verification"
)

workflow.add_edge(
    "evidence_verification",
    "citation_verification"
)

workflow.add_edge(
    "citation_verification",
    "regulatory_domain_classification"
)

workflow.add_edge(
    "regulatory_domain_classification",
    "claim_verification"
)

workflow.add_edge(
    "claim_verification",
    "consistency_check"
)

workflow.add_edge(
    "consistency_check",
    "liability_assessment"
)

workflow.add_edge(
    "liability_assessment",
    "recommendation_routing"
)

workflow.add_edge(
    "recommendation_routing",
    END
)

verification_graph = workflow.compile()


# ============================================================
# 13. RUN VERIFICATION AGENT
# ============================================================

def run_verification(investigation_result: dict):

    result = verification_graph.invoke(
        investigation_result
    )

    result["verification_summary"] = (
        f"Verification status: "
        f"{result.get('verification_status', 'UNKNOWN')}. "

        f"Liability status: "
        f"{result.get('liability_status', 'UNKNOWN')}. "

        f"Human escalation: "
        f"{result.get('human_escalation', True)}."
    )

    return result
