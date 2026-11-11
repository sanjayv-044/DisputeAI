
import re

FRAUD_CATEGORIES = [
    "Card-not-present fraud",
    "Skimming",
    "UPI social engineering",
    "Merchant dispute",
    "Duplicate charge"
]

patterns = {
    "Duplicate charge": [
        r"\bduplicate\b",
        r"\bcharged twice\b",
        r"\bdebited twice\b",
        r"\btwo charges\b",
        r"\bsame transaction twice\b",
        r"\btransaction\b.*\bappeared twice\b",
        r"\bappeared twice\b"
    ],

    "Skimming": [
        r"\bskimming\b",
        r"\bskimmer\b",
        r"\bcloned card\b",
        r"\bcard cloned\b",
        r"\bcard was cloned\b",
        r"\bcloned at an atm\b",
        r"\bcard data copied\b",
        r"\bcompromised atm\b"
    ],

    "UPI social engineering": [
        r"\bupi\b",
        r"\bqr code\b",
        r"\bcollect request\b",
        r"\bimpersonat\w*\b",
        r"\bpretend\w*\b",
        r"\botp shared\b",
        r"\botp disclosed\b"
    ],

    "Card-not-present fraud": [
        r"\bonline card\b",
        r"\bcard not present\b",
        r"\bwithout physical card\b",
        r"\bunauthori[sz]ed online card\b",
        r"\bunauthori[sz]ed online purchase\b",
        r"\bunknown online purchase\b",
        r"\bused online\b",
        r"\bcard details\b.*\bused\b",
        r"\bcard details\b.*\bonline\b",
        r"\bonline transaction\b"
    ],

    "Merchant dispute": [
        r"\brefund\b",
        r"\bproduct not received\b",
        r"\bnever received my product\b",
        r"\bnever received my order\b",
        r"\bnever received the order\b",
        r"\border not received\b",
        r"\bservice not received\b",
        r"\bservice\b.*\bnot received\b",
        r"\bwrong product\b",
        r"\bmerchant dispute\b",
        r"\bcharged but order cancelled\b",
        r"\border\b.*\bcancelled\b"
    ]
}


def classify_fraud(description):
    text = description.lower()
    scores = {}

    for category, keywords in patterns.items():
        scores[category] = sum(
            1 for pattern in keywords
            if re.search(pattern, text)
        )

    highest_score = max(scores.values())

    if highest_score == 0:
        return {
            "category": "Needs manual review",
            "confidence": "Low",
            "reason": "No clear matching indicators found."
        }

    winners = [
        category for category, score in scores.items()
        if score == highest_score
    ]

    if len(winners) > 1:
        return {
            "category": "Needs manual review",
            "confidence": "Low",
            "reason": "Multiple categories have equal matching scores."
        }

    return {
        "category": winners[0],
        "confidence": "Rule-based preliminary match",
        "reason": f"Matched indicators: {highest_score}"
    }


print("Fraud classifier updated successfully!")
