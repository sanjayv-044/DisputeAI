from datetime import date


def analyze_dispute(dispute):

    description = dispute.fraud_description.lower()

    score = 20

    fraud_type = "Other Fraud"

    # FRAUD CLASSIFICATION

    if any(word in description for word in [
        "unauthorized", "not mine", "without permission",
        "unknown transaction", "not authorized"
    ]):
        fraud_type = "Unauthorized Transaction"
        score += 25

    elif any(word in description for word in [
        "phishing", "fake link", "otp scam",
        "screen sharing", "remote access"
    ]):
        fraud_type = "Phishing / Social Engineering"
        score += 30

    elif any(word in description for word in [
        "sim swap", "account takeover", "hacked account"
    ]):
        fraud_type = "Account Takeover"
        score += 35

    elif any(word in description for word in [
        "duplicate", "charged twice", "double payment"
    ]):
        fraud_type = "Duplicate Transaction"
        score += 15

    elif any(word in description for word in [
        "skimming", "cloned card", "card cloning"
    ]):
        fraud_type = "Card Skimming"
        score += 30

    elif any(word in description for word in [
        "upi collect", "qr code", "fake upi"
    ]):
        fraud_type = "UPI Fraud"
        score += 25

    # OTP ANALYSIS

    if dispute.otp_shared:
        score += 25

    # TRANSACTION AMOUNT ANALYSIS

    if dispute.amount >= 50000:
        score += 25

    elif dispute.amount >= 10000:
        score += 15

    elif dispute.amount >= 5000:
        score += 8

    # TRANSACTION TYPE ANALYSIS

    if dispute.transaction_type == "UPI":
        if any(word in description for word in [
            "collect request", "qr code", "upi scam"
        ]):
            score += 10

    # DATE ANALYSIS

    try:
        transaction_date = date.fromisoformat(
            str(dispute.transaction_date)
        )

        reported_date = date.fromisoformat(
            str(dispute.reported_date)
        )

        reporting_delay = (
            reported_date - transaction_date
        ).days

        if reporting_delay <= 1:
            score += 10

        elif reporting_delay > 30:
            score += 5

    except (ValueError, TypeError):
        pass

    # FINAL RISK SCORE

    score = min(max(score, 0), 100)

    # PRIORITY ASSIGNMENT

    if score >= 80:
        priority = "Critical"

    elif score >= 60:
        priority = "High"

    elif score >= 35:
        priority = "Medium"

    else:
        priority = "Low"

    # HUMAN ESCALATION

    escalated = score >= 80

    # RECOMMENDATION ENGINE

    if priority == "Critical":

        recommendation = (
            "Immediately escalate to the fraud investigation team. "
            "Review transaction evidence and initiate urgent investigation."
        )

    elif priority == "High":

        recommendation = (
            "Prioritize this dispute for manual verification. "
            "Check transaction records and customer authentication details."
        )

    elif priority == "Medium":

        recommendation = (
            "Verify transaction details, customer complaint "
            "and available supporting evidence."
        )

    else:

        recommendation = (
            "Place the dispute in the standard review queue "
            "and verify the submitted information."
        )

    return {
        "fraud_type": fraud_type,
        "risk_score": score,
        "priority": priority,
        "escalated": escalated,
        "recommendation": recommendation
    }