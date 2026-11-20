"""
DisputeAI Fraud Classification Module
Identifies the 5 canonical banking fraud categories:
1. UPI Fraud
2. Credit/Debit Card Fraud
3. Phishing Fraud
4. Internet Banking Fraud
5. Identity Theft

Generates risk score (0-100), risk level (Low, Medium, High, Critical),
priority (Low, Medium, High, Critical), and detailed explanation.
"""

import re
from typing import Dict, Any, Optional

CANONICAL_CATEGORIES = [
    "UPI Fraud",
    "Credit/Debit Card Fraud",
    "Phishing Fraud",
    "Internet Banking Fraud",
    "Identity Theft"
]

CATEGORY_PATTERNS = {
    "UPI Fraud": [
        r"\bupi\b",
        r"\bqr\s*code\b",
        r"\bcollect\s*request\b",
        r"\bgpay\b",
        r"\bgoogle\s*pay\b",
        r"\bphonepe\b",
        r"\bpaytm\b",
        r"\bvpa\b",
        r"\bscan(?:ned)?\s*(?:and\s*pay|qr)\b",
        r"\bfake\s*upi\b",
        r"\bupi\s*pin\b",
        r"\binstant\s*transfer\b.*\bupi\b"
    ],

    "Credit/Debit Card Fraud": [
        r"\b(?:credit|debit|atm|forex|prepaid|smart)\s*card\b",
        r"(?<!pan\s)(?<!aadhaar\s)\bcard\b",
        r"\bcard-not-present\b",
        r"\bwithout\s*(?:my\s*)?physical\s*card\b",
        r"\bunauthori[sz]ed\s*(?:online\s*)?card\b",
        r"\bcard\s*details\s*used\b",
        r"\bcard\s*number\b",
        r"\bcvv\b",
        r"\batm\b",
        r"\bskimming\b",
        r"\bskimmer\b",
        r"\bcloned\s*card\b",
        r"\bcard\s*was\s*cloned\b",
        r"\bpos\s*machine\b",
        r"\bduplicate\s*(?:charge|transaction|payment)\b",
        r"\bcharged\s*twice\b",
        r"\bdebited\s*twice\b",
        r"\bmerchant\s*dispute\b"
    ],

    "Phishing Fraud": [
        r"\bphishing\b",
        r"\bfake\s*link\b",
        r"\bmalicious\s*link\b",
        r"\bsuspicious\s*(?:link|sms|message)\b",
        r"\blottery\b",
        r"\bcaller\s*impersonat\w*\b",
        r"\bpretend\w*\s*(?:to\s*be\s*bank|bank\s*officer|manager)\b",
        r"\btricked\s*into\b",
        r"\bsocial\s*engineering\b",
        r"\bscreen\s*sharing\b",
        r"\bremote\s*access\b",
        r"\banydesk\b",
        r"\bteamviewer\b",
        r"\bvishing\b",
        r"\botp\s*(?:scam|trick|shared|disclosed)\b"
    ],

    "Internet Banking Fraud": [
        r"\binternet\s*banking\b",
        r"\bnet\s*banking\b",
        r"\bnetbanking\b",
        r"\bonline\s*banking\b",
        r"\bbank\s*portal\b",
        r"\bunauthori[sz]ed\s*(?:neft|rtgs|imps)\b",
        r"\bunauthori[sz]ed\s*beneficiary\b",
        r"\bbeneficiary\s*added\b",
        r"\blogin\s*credentials?\b",
        r"\bpassword\s*compromised\b",
        r"\bsession\s*(?:hijack|compromised)\b"
    ],

    "Identity Theft": [
        r"\bidentity\s*theft\b",
        r"\bsim\s*swap\b",
        r"\bduplicate\s*sim\b",
        r"\bsim\s*deactivated\b",
        r"\bstolen\s*(?:identity|aadhaar|pan|documents)\b",
        r"\bkyc\s*(?:fraud|scam|stolen)\b",
        r"\baccount\s*takeover\b",
        r"\bhacked\s*account\b",
        r"\bloan\s*(?:in\s*my\s*name|taken\s*fraudulently)\b"
    ]
}


def classify_fraud(description: str, otp_shared: bool = False, amount: float = 0.0, transaction_type: str = "") -> Dict[str, Any]:
    """
    Performs multi-criteria fraud classification.
    Returns:
    - category: One of the 5 canonical fraud categories
    - risk_score: 0 to 100
    - risk_level: Low, Medium, High, Critical
    - priority: Low, Medium, High, Critical
    - explanation: Diagnostic reasoning based on detected indicators
    """
    text = (description or "").lower()
    scores = {}
    matched_patterns = {}

    for cat, regex_list in CATEGORY_PATTERNS.items():
        matches = [p for p in regex_list if re.search(p, text)]
        scores[cat] = len(matches)
        matched_patterns[cat] = matches

    # Contextual hints from transaction type
    if (transaction_type or "").upper() == "UPI":
        scores["UPI Fraud"] = scores.get("UPI Fraud", 0) + 1
    elif (transaction_type or "").upper() == "CARD":
        scores["Credit/Debit Card Fraud"] = scores.get("Credit/Debit Card Fraud", 0) + 1

    max_matches = max(scores.values()) if scores else 0

    if max_matches == 0:
        # Fallback to transaction type or general card fraud
        if (transaction_type or "").upper() == "UPI":
            predicted_category = "UPI Fraud"
        elif (transaction_type or "").upper() == "CARD":
            predicted_category = "Credit/Debit Card Fraud"
        else:
            predicted_category = "Credit/Debit Card Fraud"
        confidence = "Low"
        reason = "Classified based on transaction channel; detailed patterns unobserved."
    else:
        # Choose category with highest matched indicators
        candidates = [cat for cat, s in scores.items() if s == max_matches]
        predicted_category = candidates[0]
        confidence = "High" if max_matches >= 2 else "Medium"
        reason = f"Matched {max_matches} pattern indicator(s): {', '.join(matched_patterns[predicted_category][:3])}"

    # Calculate Risk Score (0-100)
    base_scores = {
        "Identity Theft": 45,
        "Phishing Fraud": 35,
        "Internet Banking Fraud": 35,
        "UPI Fraud": 25,
        "Credit/Debit Card Fraud": 25
    }
    score = base_scores.get(predicted_category, 25)

    # Factor 1: OTP Disclosed (+30)
    if otp_shared:
        score += 30

    # Factor 2: Transaction Amount
    if amount >= 100000:
        score += 30
    elif amount >= 50000:
        score += 20
    elif amount >= 25000:
        score += 15
    elif amount >= 10000:
        score += 10
    elif amount >= 5000:
        score += 5

    # Factor 3: High-Risk keywords
    if any(k in text for k in ["hacked", "stolen", "unauthorized", "urgent", "lost life savings", "fir", "police"]):
        score += 10

    # Bound score
    score = min(max(score, 10), 100)

    # Determine Risk Level & Priority
    if score >= 85:
        risk_level = "Critical"
        priority = "Critical"
    elif score >= 65:
        risk_level = "High"
        priority = "High"
    elif score >= 40:
        risk_level = "Medium"
        priority = "Medium"
    else:
        risk_level = "Low"
        priority = "Low"

    explanation = (
        f"Classified as '{predicted_category}' ({confidence} confidence). {reason}. "
        f"Assigned Risk Score of {score}/100 ({risk_level} Risk). "
        f"{'OTP was compromised by third party. ' if otp_shared else ''}"
        f"{'High transaction exposure (>= ₹50,000). ' if amount >= 50000 else ''}"
    )

    return {
        "category": predicted_category,
        "risk_score": score,
        "risk_level": risk_level,
        "priority": priority,
        "confidence": confidence,
        "reason": reason,
        "explanation": explanation
    }
