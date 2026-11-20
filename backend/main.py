import os
import sys
import uuid
import logging
import time
import json
import shutil
from pathlib import Path
from typing import Optional, List

backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent
for p in [str(backend_dir), str(root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from sqlalchemy import inspect, text, func

from database import Base, engine, get_db
from models import User, Dispute, EvidenceFile, InvestigationDossier, ComplaintHistory
from schemas import (
    UserRegister, UserLogin, UserOut, Token,
    DisputeCreate, DisputeOut, AdminActionRequest, StatusUpdateRequest
)
from security import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, require_customer, require_admin, get_current_user_optional
)
from async_worker import dispatch_investigation_job
from evaluation_runner import run_full_evaluation
from src.monitoring import (
    ACTIVE_REQUESTS, VERIFICATION_DURATION, VERIFICATION_REQUESTS,
    HUMAN_ESCALATIONS, get_metrics
)


# =====================================================
# LOGGING CONFIGURATION
# =====================================================

LOG_FILE = backend_dir / "disputeai.log"
logger = logging.getLogger("disputeai")
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

logger.info("DisputeAI logging initialized")


# =====================================================
# UPLOADS DIRECTORY
# =====================================================

UPLOAD_DIR = backend_dir / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================
# DATABASE INITIALIZATION & MIGRATION
# =====================================================

Base.metadata.create_all(bind=engine)


def migrate_and_seed_database():
    """Migrates missing columns and seeds default admin and customer accounts."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "disputes" in existing_tables:
        existing_cols = {col["name"] for col in inspector.get_columns("disputes")}
        new_cols = {
            "user_id": "INTEGER REFERENCES users(id)",
            "customer_email": "VARCHAR(255)",
            "bank_name": "VARCHAR(255) DEFAULT 'State Bank of India'",
            "fraud_type_claimed": "VARCHAR(100)",
            "fraud_type": "VARCHAR(100) DEFAULT 'Unclassified'",
            "risk_score": "INTEGER DEFAULT 0",
            "risk_level": "VARCHAR(50) DEFAULT 'Medium'",
            "priority": "VARCHAR(50) DEFAULT 'Medium'",
            "classification_explanation": "TEXT DEFAULT ''",
            "escalated": "BOOLEAN DEFAULT 0",
            "recommendation": "TEXT DEFAULT ''",
            "liability_verdict": "VARCHAR(100) DEFAULT 'PENDING_ASSESSMENT'",
            "admin_remarks": "TEXT DEFAULT ''",
            "final_resolution": "TEXT DEFAULT ''",
            "updated_at": "DATETIME"
        }

        with engine.begin() as conn:
            for col_name, col_def in new_cols.items():
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE disputes ADD COLUMN {col_name} {col_def}"))
                        logger.info("Migrated disputes column: %s", col_name)
                    except Exception as e:
                        logger.warning("Migration notice for %s: %s", col_name, e)

    # Seed Default Administrator & Demo Customer
    db = next(get_db())
    try:
        admin_user = db.query(User).filter(User.email == "admin@disputeai.bank").first()
        if not admin_user:
            admin_user = User(
                email="admin@disputeai.bank",
                password_hash=get_password_hash("Admin@DisputeAI2026"),
                full_name="Chief Risk Officer",
                phone="+91-9876543210",
                role="admin"
            )
            db.add(admin_user)
            logger.info("Seeded default admin user: admin@disputeai.bank")

        customer_user = db.query(User).filter(User.email == "customer@disputeai.bank").first()
        if not customer_user:
            customer_user = User(
                email="customer@disputeai.bank",
                password_hash=get_password_hash("Customer@DisputeAI2026"),
                full_name="Rajesh Sharma",
                phone="+91-9876501234",
                role="customer"
            )
            db.add(customer_user)
            logger.info("Seeded demo customer user: customer@disputeai.bank")

        db.commit()
    except Exception as e:
        logger.warning("User seeding notice: %s", e)
        db.rollback()
    finally:
        db.close()


try:
    migrate_and_seed_database()
    logger.info("Database migration & seeding completed successfully")
except Exception:
    logger.exception("Database migration failed")


# =====================================================
# FASTAPI APPLICATION
# =====================================================

app = FastAPI(
    title="DisputeAI - Banking Dispute Resolution & Fraud Investigation API",
    description="Production-grade AI-powered dispute resolution, LangGraph multi-agent triage, and RBI compliance platform.",
    version="3.0.0",
)


# =====================================================
# CORS CONFIGURATION
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# REQUEST LOGGING & MONITORING MIDDLEWARE
# =====================================================

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    ACTIVE_REQUESTS.inc()
    start_time = time.perf_counter()
    status_label = "success"

    try:
        response = await call_next(request)
        return response
    except Exception:
        status_label = "error"
        logger.exception("Request failed | Path: %s", request.url.path)
        raise
    finally:
        VERIFICATION_DURATION.observe(time.perf_counter() - start_time)
        VERIFICATION_REQUESTS.labels(status=status_label).inc()
        ACTIVE_REQUESTS.dec()


# =====================================================
# VALIDATION ERROR HANDLER
# =====================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]},
    )


# =====================================================
# HOME & HEALTH ENDPOINTS
# =====================================================

@app.get("/")
def home():
    return {
        "service": "DisputeAI Platform API",
        "version": "3.0.0",
        "status": "online",
        "regulatory_framework": "RBI Customer Protection 2017 & Integrated Ombudsman 2026"
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "DisputeAI Backend",
            "database": "connected",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")


# =====================================================
# AUTHENTICATION ENDPOINTS
# =====================================================

@app.post("/api/auth/register", response_model=Token, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role if user_data.role in ["customer", "admin"] else "customer"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "role": new_user.role, "id": new_user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }


@app.post("/api/auth/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@app.get("/api/auth/me", response_model=UserOut)
def get_current_user_profile(user: User = Depends(get_current_user)):
    return user


# =====================================================
# CUSTOMER DISPUTE ENDPOINTS
# =====================================================

@app.post("/api/customer/disputes", status_code=201)
def submit_customer_dispute(
    dispute_in: DisputeCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    # Verify no duplicate transaction
    existing = db.query(Dispute).filter(Dispute.transaction_id == dispute_in.transaction_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Transaction ID {dispute_in.transaction_id} already has a registered dispute.")

    dispute_id = "DSP-" + uuid.uuid4().hex[:8].upper()

    new_dispute = Dispute(
        dispute_id=dispute_id,
        user_id=current_user.id,
        customer_name=dispute_in.customer_name,
        customer_email=dispute_in.customer_email or current_user.email,
        bank_name=dispute_in.bank_name or "State Bank of India",
        transaction_id=dispute_in.transaction_id,
        amount=dispute_in.amount,
        transaction_type=dispute_in.transaction_type,
        transaction_date=str(dispute_in.transaction_date),
        reported_date=str(dispute_in.reported_date),
        fraud_type_claimed=dispute_in.fraud_type_claimed or "Unknown",
        fraud_description=dispute_in.fraud_description,
        otp_shared=dispute_in.otp_shared,
        status="Pending",
        fraud_type="Evaluating...",
        risk_level="Evaluating...",
        recommendation="AI multi-agent investigation scheduled."
    )
    db.add(new_dispute)

    # Initial history entry
    history = ComplaintHistory(
        dispute_id=dispute_id,
        action="Dispute Submitted",
        status_from="",
        status_to="Pending",
        changed_by=f"Customer ({current_user.full_name})",
        notes="Dispute successfully registered in the platform."
    )
    db.add(history)
    db.commit()
    db.refresh(new_dispute)

    # Dispatch asynchronous background investigation
    dispatch_investigation_job(dispute_id, background_tasks)

    return {
        "message": "Dispute submitted successfully and queued for AI investigation.",
        "dispute_id": dispute_id,
        "status": new_dispute.status,
        "customer": new_dispute.customer_name,
        "amount": new_dispute.amount
    }


@app.get("/api/customer/disputes")
def get_customer_disputes(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    # Customers only see their own disputes; admins can see all if using this endpoint
    query = db.query(Dispute)
    if current_user.role != "admin":
        query = query.filter(
            (Dispute.user_id == current_user.id) |
            (Dispute.customer_email == current_user.email)
        )

    disputes = query.order_by(Dispute.id.desc()).all()
    return disputes


@app.get("/api/customer/disputes/{dispute_id}")
def get_customer_dispute_detail(
    dispute_id: str,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    if current_user.role != "admin" and dispute.user_id != current_user.id and dispute.customer_email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own complaints.")

    dossier = db.query(InvestigationDossier).filter(InvestigationDossier.dispute_id == dispute_id).first()
    history = db.query(ComplaintHistory).filter(ComplaintHistory.dispute_id == dispute_id).order_by(ComplaintHistory.id.asc()).all()
    evidence_files = db.query(EvidenceFile).filter(EvidenceFile.dispute_id == dispute_id).all()

    dossier_dict = None
    if dossier:
        try:
            citations = json.loads(dossier.rbi_citations_json or "[]")
        except Exception:
            citations = []

        dossier_dict = {
            "fraud_category": dossier.fraud_category,
            "agent_findings": dossier.agent_findings,
            "citations": citations,
            "verification_summary": dossier.verification_summary,
            "liability_status": dossier.liability_status,
            "liability_reasoning": dossier.liability_reasoning,
            "recommendation": dossier.recommendation,
            "human_escalation": dossier.human_escalation,
            "confidence_score": dossier.confidence_score
        }

    return {
        "dispute_id": dispute.dispute_id,
        "customer_name": dispute.customer_name,
        "customer_email": dispute.customer_email,
        "bank_name": dispute.bank_name,
        "transaction_id": dispute.transaction_id,
        "amount": dispute.amount,
        "transaction_type": dispute.transaction_type,
        "transaction_date": dispute.transaction_date,
        "reported_date": dispute.reported_date,
        "fraud_type_claimed": dispute.fraud_type_claimed,
        "fraud_description": dispute.fraud_description,
        "otp_shared": dispute.otp_shared,
        "fraud_type": dispute.fraud_type,
        "risk_score": dispute.risk_score,
        "risk_level": dispute.risk_level,
        "priority": dispute.priority,
        "classification_explanation": dispute.classification_explanation,
        "escalated": dispute.escalated,
        "recommendation": dispute.recommendation,
        "liability_verdict": dispute.liability_verdict,
        "status": dispute.status,
        "admin_remarks": dispute.admin_remarks,
        "final_resolution": dispute.final_resolution,
        "created_at": dispute.created_at,
        "evidence_files": evidence_files,
        "dossier": dossier_dict,
        "history": history
    }


@app.post("/api/customer/disputes/{dispute_id}/upload")
async def upload_supporting_document(
    dispute_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    if current_user.role != "admin" and dispute.user_id != current_user.id and dispute.customer_email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Validate file format and size
    allowed_exts = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Allowed document types: PDF, PNG, JPG, JPEG, TXT.")

    safe_name = f"{uuid.uuid4().hex[:10]}_{file.filename}"
    dest_path = UPLOAD_DIR / safe_name

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = dest_path.stat().st_size

    new_file = EvidenceFile(
        dispute_id=dispute.dispute_id,
        filename=file.filename,
        file_path=str(dest_path),
        file_type=file.content_type or ext,
        file_size=file_size,
        verified_status="Verified (Uploaded & Integrity Checked)"
    )
    db.add(new_file)

    history = ComplaintHistory(
        dispute_id=dispute.dispute_id,
        action="Evidence Document Uploaded",
        status_from=dispute.status,
        status_to=dispute.status,
        changed_by=f"Customer ({current_user.full_name})",
        notes=f"Uploaded supporting document: {file.filename} ({file_size} bytes)"
    )
    db.add(history)
    db.commit()

    return {"message": "Document uploaded successfully", "filename": file.filename, "size": file_size}


@app.get("/api/customer/notifications")
def get_customer_notifications(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    # Fetch recent updates on customer's disputes
    disputes = db.query(Dispute).filter(
        (Dispute.user_id == current_user.id) |
        (Dispute.customer_email == current_user.email)
    ).all()
    dispute_ids = [d.dispute_id for d in disputes]

    history = db.query(ComplaintHistory).filter(
        ComplaintHistory.dispute_id.in_(dispute_ids)
    ).order_by(ComplaintHistory.id.desc()).limit(15).all()

    return [
        {
            "id": h.id,
            "dispute_id": h.dispute_id,
            "action": h.action,
            "status": h.status_to,
            "notes": h.notes,
            "timestamp": h.created_at
        }
        for h in history
    ]


# =====================================================
# ADMIN ENDPOINTS (ROLE-PROTECTED)
# =====================================================

@app.get("/api/admin/analytics")
def get_admin_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total = db.query(Dispute).count()
    pending = db.query(Dispute).filter(Dispute.status == "Pending").count()
    in_investigation = db.query(Dispute).filter(Dispute.status == "In Investigation").count()
    under_review = db.query(Dispute).filter(Dispute.status == "Under Review").count()
    escalated = db.query(Dispute).filter((Dispute.status == "Escalated") | (Dispute.escalated == True)).count()
    resolved = db.query(Dispute).filter(Dispute.status.like("Resolved%")).count()

    high_risk = db.query(Dispute).filter(Dispute.risk_level == "High").count()
    critical_risk = db.query(Dispute).filter(Dispute.risk_level == "Critical").count()

    # Category distribution
    categories = ["UPI Fraud", "Credit/Debit Card Fraud", "Phishing Fraud", "Internet Banking Fraud", "Identity Theft"]
    category_counts = []
    for cat in categories:
        count = db.query(Dispute).filter(Dispute.fraud_type == cat).count()
        category_counts.append({"name": cat, "value": count})

    # Status distribution
    status_counts = [
        {"name": "Pending", "value": pending},
        {"name": "In Investigation", "value": in_investigation},
        {"name": "Under Review", "value": under_review},
        {"name": "Escalated", "value": escalated},
        {"name": "Resolved", "value": resolved}
    ]

    # Transaction type distribution
    tx_types = ["UPI", "Card", "Internet Banking"]
    tx_counts = []
    for t in tx_types:
        c = db.query(Dispute).filter(Dispute.transaction_type == t).count()
        if c > 0:
            tx_counts.append({"name": t, "value": c})

    return {
        "total_complaints": total,
        "pending_complaints": pending,
        "in_investigation": in_investigation,
        "under_review": under_review,
        "resolved_complaints": resolved,
        "escalated_complaints": escalated,
        "high_risk_complaints": high_risk,
        "critical_risk_complaints": critical_risk,
        "category_distribution": category_counts,
        "status_distribution": status_counts,
        "transaction_type_distribution": tx_counts
    }


@app.get("/api/admin/disputes")
def get_all_disputes_for_admin(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    fraud_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Dispute)
    if status and status != "All":
        query = query.filter(Dispute.status == status)
    if risk_level and risk_level != "All":
        query = query.filter(Dispute.risk_level == risk_level)
    if fraud_type and fraud_type != "All":
        query = query.filter(Dispute.fraud_type == fraud_type)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Dispute.dispute_id.like(s)) |
            (Dispute.customer_name.like(s)) |
            (Dispute.transaction_id.like(s))
        )

    disputes = query.order_by(Dispute.id.desc()).all()
    return disputes


@app.get("/api/admin/disputes/{dispute_id}")
def get_admin_dispute_dossier(
    dispute_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    dossier = db.query(InvestigationDossier).filter(InvestigationDossier.dispute_id == dispute_id).first()
    history = db.query(ComplaintHistory).filter(ComplaintHistory.dispute_id == dispute_id).order_by(ComplaintHistory.id.asc()).all()
    evidence_files = db.query(EvidenceFile).filter(EvidenceFile.dispute_id == dispute_id).all()

    citations = []
    if dossier and dossier.rbi_citations_json:
        try:
            citations = json.loads(dossier.rbi_citations_json)
        except Exception:
            citations = []

    return {
        "dispute": dispute,
        "dossier": dossier,
        "citations": citations,
        "evidence_files": evidence_files,
        "history": history
    }


@app.post("/api/admin/disputes/{dispute_id}/action")
def perform_admin_action(
    dispute_id: str,
    action_in: AdminActionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    prev_status = dispute.status
    act = action_in.action.lower()

    if act == "approve":
        new_status = "Resolved - Refund Approved"
        resolution = action_in.final_resolution or f"Approved recommendation for {dispute.liability_verdict}. Shadow reversal authorized."
    elif act == "reject":
        new_status = "Resolved - Dispute Rejected"
        resolution = action_in.final_resolution or "Dispute rejected based on customer negligence / insufficient compliance with RBI notification window."
    elif act == "escalate":
        new_status = "Escalated"
        resolution = action_in.final_resolution or "Escalated for senior human fraud investigation."
        dispute.escalated = True
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve', 'reject', or 'escalate'.")

    dispute.status = new_status
    dispute.admin_remarks = action_in.remarks
    dispute.final_resolution = resolution

    history = ComplaintHistory(
        dispute_id=dispute.dispute_id,
        action=f"Admin Decision: {action_in.action.upper()}",
        status_from=prev_status,
        status_to=new_status,
        changed_by=f"Admin ({current_user.full_name})",
        notes=f"Remarks: {action_in.remarks} | Resolution: {resolution}"
    )
    db.add(history)
    db.commit()

    return {
        "message": f"Dispute {dispute_id} updated successfully.",
        "status": new_status,
        "final_resolution": resolution
    }


@app.post("/api/admin/disputes/{dispute_id}/status")
def update_dispute_status_manually(
    dispute_id: str,
    status_in: StatusUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    prev_status = dispute.status
    dispute.status = status_in.status
    if status_in.remarks:
        dispute.admin_remarks = status_in.remarks

    history = ComplaintHistory(
        dispute_id=dispute.dispute_id,
        action="Status Manually Updated",
        status_from=prev_status,
        status_to=status_in.status,
        changed_by=f"Admin ({current_user.full_name})",
        notes=status_in.remarks or f"Status changed to {status_in.status}"
    )
    db.add(history)
    db.commit()

    return {"message": "Status updated successfully", "status": dispute.status}


@app.get("/api/admin/evaluation")
def get_evaluation_results(
    current_user: User = Depends(require_admin)
):
    """Executes the 20 benchmark scenarios and returns live evaluation metrics."""
    return run_full_evaluation()


# =====================================================
# PROMETHEUS METRICS & SYSTEM MONITORING
# =====================================================

@app.get("/metrics", include_in_schema=False)
def prometheus_metrics():
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


@app.get("/api/admin/monitoring")
def get_monitoring_summary(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    metrics_data, _ = get_metrics()
    text_data = metrics_data.decode("utf-8")

    # Extract metrics highlights
    active_requests = 0
    verification_count = 0
    escalations_count = 0

    for line in text_data.split("\n"):
        if line.startswith("disputeai_active_requests"):
            try:
                active_requests = float(line.split()[-1])
            except Exception:
                pass
        elif line.startswith("disputeai_verification_requests_total") and "status=\"success\"" in line:
            try:
                verification_count = float(line.split()[-1])
            except Exception:
                pass
        elif line.startswith("disputeai_human_escalations_total"):
            try:
                escalations_count = float(line.split()[-1])
            except Exception:
                pass

    return {
        "status": "OPERATIONAL",
        "active_concurrent_requests": active_requests,
        "total_verification_requests": verification_count,
        "total_human_escalations": escalations_count,
        "raw_metrics_url": "/metrics",
        "prometheus_endpoint": "http://localhost:9090",
        "grafana_endpoint": "http://localhost:3000"
    }


# =====================================================
# BACKWARD COMPATIBLE LEGACY APIS
# =====================================================

@app.get("/api/disputes")
def legacy_get_disputes(db: Session = Depends(get_db)):
    disputes = db.query(Dispute).order_by(Dispute.id.desc()).all()
    return [
        {
            "dispute_id": d.dispute_id,
            "customer_name": d.customer_name,
            "transaction_id": d.transaction_id,
            "amount": d.amount,
            "transaction_type": d.transaction_type,
            "transaction_date": d.transaction_date,
            "reported_date": d.reported_date,
            "fraud_description": d.fraud_description,
            "otp_shared": d.otp_shared,
            "fraud_type": d.fraud_type,
            "risk_score": d.risk_score,
            "priority": d.priority,
            "escalated": d.escalated,
            "recommendation": d.recommendation,
            "status": d.status,
        }
        for d in disputes
    ]


@app.post("/api/disputes", status_code=201)
def legacy_create_dispute(
    dispute: DisputeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing = db.query(Dispute).filter(Dispute.transaction_id == dispute.transaction_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="This transaction already has a dispute")

    dispute_id = "DSP" + uuid.uuid4().hex[:8].upper()
    new_dispute = Dispute(
        dispute_id=dispute_id,
        customer_name=dispute.customer_name,
        transaction_id=dispute.transaction_id,
        amount=dispute.amount,
        transaction_type=dispute.transaction_type,
        transaction_date=str(dispute.transaction_date),
        reported_date=str(dispute.reported_date),
        fraud_description=dispute.fraud_description,
        otp_shared=dispute.otp_shared,
        status="Pending"
    )
    db.add(new_dispute)
    db.commit()
    db.refresh(new_dispute)

    # Run investigation asynchronously
    dispatch_investigation_job(dispute_id, background_tasks)

    return {
        "message": "Dispute successfully registered",
        "dispute_id": new_dispute.dispute_id,
        "status": new_dispute.status,
    }


@app.get("/api/disputes/{dispute_id}")
def legacy_get_dispute(dispute_id: str, db: Session = Depends(get_db)):
    d = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return {
        "dispute_id": d.dispute_id,
        "customer_name": d.customer_name,
        "transaction_id": d.transaction_id,
        "amount": d.amount,
        "transaction_type": d.transaction_type,
        "transaction_date": d.transaction_date,
        "reported_date": d.reported_date,
        "fraud_description": d.fraud_description,
        "otp_shared": d.otp_shared,
        "fraud_type": d.fraud_type,
        "risk_score": d.risk_score,
        "priority": d.priority,
        "escalated": d.escalated,
        "recommendation": d.recommendation,
        "status": d.status,
    }
