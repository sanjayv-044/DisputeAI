"""
DisputeAI Asynchronous Background Worker
Handles background processing of AI multi-agent investigation.
Supports Celery/Redis queue when available, with automatic graceful
in-process background execution fallback.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent
for p in [str(backend_dir), str(root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from database import SessionLocal
from models import Dispute, InvestigationDossier, ComplaintHistory
from src.multi_agent_workflow import run_multi_agent_investigation

logger = logging.getLogger("disputeai.worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Optional Celery App
celery_app = None
try:
    from celery import Celery
    celery_app = Celery("disputeai_tasks", broker=REDIS_URL, backend=REDIS_URL)
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_ignore_result=False,
    )
except Exception:
    celery_app = None


def execute_dispute_investigation(dispute_id: str):
    """
    Main asynchronous processing routine:
    1. Reads dispute from DB
    2. Runs 4-Agent LangGraph workflow (Investigation, Verification, Liability, Recommendation)
    3. Persists classification, dossier, and status updates
    4. Records complaint audit history
    """
    logger.info("Starting background AI investigation for dispute: %s", dispute_id)
    db = SessionLocal()
    try:
        dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
        if not dispute:
            logger.error("Dispute not found for background investigation: %s", dispute_id)
            return

        # Update status to In Investigation
        prev_status = dispute.status
        dispute.status = "In Investigation"
        db.commit()

        # Build payload for multi-agent workflow
        payload = {
            "dispute_id": dispute.dispute_id,
            "customer_name": dispute.customer_name,
            "customer_email": dispute.customer_email or "",
            "bank_name": dispute.bank_name or "State Bank of India",
            "transaction_id": dispute.transaction_id,
            "amount": dispute.amount,
            "transaction_type": dispute.transaction_type,
            "transaction_date": dispute.transaction_date,
            "reported_date": dispute.reported_date,
            "fraud_type_claimed": dispute.fraud_type_claimed or "",
            "fraud_description": dispute.fraud_description,
            "otp_shared": dispute.otp_shared,
            "evidence_files": [
                {"filename": f.filename, "file_size": f.file_size, "file_type": f.file_type}
                for f in dispute.evidence_files
            ]
        }

        # Run 4-agent LangGraph workflow
        agent_result = run_multi_agent_investigation(payload)

        # Update dispute with AI findings
        dispute.fraud_type = agent_result.get("fraud_category", "Unclassified")
        dispute.risk_score = agent_result.get("risk_score", 0)
        dispute.risk_level = agent_result.get("risk_level", "Medium")
        dispute.priority = agent_result.get("priority", "Medium")
        dispute.classification_explanation = agent_result.get("classification_explanation", "")
        dispute.escalated = agent_result.get("human_escalation", False)
        dispute.recommendation = agent_result.get("recommendation", "")
        dispute.liability_verdict = agent_result.get("liability_status", "PENDING_ASSESSMENT")

        # Determine target status
        if dispute.escalated:
            new_status = "Escalated"
        else:
            new_status = "Under Review"

        dispute.status = new_status

        # Create or update dossier
        dossier_data = agent_result.get("final_dossier", {})
        existing_dossier = db.query(InvestigationDossier).filter(InvestigationDossier.dispute_id == dispute_id).first()
        if not existing_dossier:
            new_dossier = InvestigationDossier(
                dispute_id=dispute.dispute_id,
                fraud_category=dispute.fraud_type,
                agent_findings=agent_result.get("investigation_findings", ""),
                rbi_citations_json=json.dumps(agent_result.get("citation_verification", [])),
                verification_summary=agent_result.get("verification_summary", ""),
                liability_status=dispute.liability_verdict,
                liability_reasoning=agent_result.get("liability_reasoning", ""),
                recommendation=dispute.recommendation,
                human_escalation=dispute.escalated,
                confidence_score=agent_result.get("confidence_score", 0.85)
            )
            db.add(new_dossier)
        else:
            existing_dossier.fraud_category = dispute.fraud_type
            existing_dossier.agent_findings = agent_result.get("investigation_findings", "")
            existing_dossier.rbi_citations_json = json.dumps(agent_result.get("citation_verification", []))
            existing_dossier.verification_summary = agent_result.get("verification_summary", "")
            existing_dossier.liability_status = dispute.liability_verdict
            existing_dossier.liability_reasoning = agent_result.get("liability_reasoning", "")
            existing_dossier.recommendation = dispute.recommendation
            existing_dossier.human_escalation = dispute.escalated
            existing_dossier.confidence_score = agent_result.get("confidence_score", 0.85)

        # Record History Log
        history = ComplaintHistory(
            dispute_id=dispute.dispute_id,
            action="AI Multi-Agent Investigation Completed",
            status_from=prev_status,
            status_to=new_status,
            changed_by="LangGraph Multi-Agent Engine",
            notes=(
                f"Fraud Category: {dispute.fraud_type} | Risk: {dispute.risk_score} ({dispute.risk_level}) | "
                f"Liability: {dispute.liability_verdict} | Escalated: {dispute.escalated}"
            )
        )
        db.add(history)

        db.commit()
        logger.info(
            "Background investigation completed for %s | Status: %s | Liability: %s",
            dispute_id, new_status, dispute.liability_verdict
        )

    except Exception:
        logger.exception("Error executing background investigation for %s", dispute_id)
        db.rollback()
    finally:
        db.close()


if celery_app:
    @celery_app.task(name="investigate_dispute_task")
    def celery_investigate_dispute(dispute_id: str):
        execute_dispute_investigation(dispute_id)


def dispatch_investigation_job(dispute_id: str, background_tasks = None):
    """
    Dispatches investigation task to Celery queue if available,
    otherwise queues it with FastAPI background_tasks.
    """
    dispatched_celery = False
    if celery_app and os.getenv("USE_CELERY", "").lower() in ["1", "true"]:
        try:
            celery_app.send_task("investigate_dispute_task", args=[dispute_id])
            logger.info("Investigation job queued in Celery/Redis for %s", dispute_id)
            dispatched_celery = True
        except Exception as e:
            logger.warning("Celery dispatch failed (%s), using BackgroundTasks fallback", e)

    if not dispatched_celery:
        if background_tasks:
            background_tasks.add_task(execute_dispute_investigation, dispute_id)
            logger.info("Investigation job queued via BackgroundTasks for %s", dispute_id)
        else:
            # Synchronous execution if no background tasks provided
            execute_dispute_investigation(dispute_id)
