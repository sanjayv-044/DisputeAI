import uuid
import logging
import time

from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from sqlalchemy.orm import Session
from sqlalchemy import inspect, text

from database import Base, engine, get_db
from models import Dispute
from schemas import DisputeCreate
from ai_engine import analyze_dispute

from src.monitoring import (
    ACTIVE_REQUESTS,
    VERIFICATION_DURATION,
    VERIFICATION_REQUESTS,
    HUMAN_ESCALATIONS,
    get_metrics,
)


# =====================================================
# LOGGING CONFIGURATION
# =====================================================

LOG_FILE = Path(__file__).resolve().parent / "disputeai.log"

logger = logging.getLogger("disputeai")
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

logger.info("DisputeAI logging initialized")


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

Base.metadata.create_all(bind=engine)


# =====================================================
# DATABASE MIGRATION
# =====================================================

def migrate_database():
    columns = {
        "fraud_type": "VARCHAR DEFAULT 'Unclassified'",
        "risk_score": "INTEGER DEFAULT 0",
        "priority": "VARCHAR DEFAULT 'Medium'",
        "escalated": "BOOLEAN DEFAULT 0",
        "recommendation": "TEXT DEFAULT ''",
    }

    inspector = inspect(engine)

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("disputes")
    }

    with engine.begin() as connection:
        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE disputes "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )

                logger.info(
                    "Database migration completed: %s",
                    column_name,
                )


try:
    migrate_database()
    logger.info("Database initialized successfully")
except Exception:
    logger.exception("Database initialization failed")
    raise


# =====================================================
# FASTAPI APPLICATION
# =====================================================

app = FastAPI(
    title="Card Dispute Triage API",
    description="AI-powered banking dispute management system",
    version="2.0.0",
)


# =====================================================
# CORS CONFIGURATION
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# REQUEST LOGGING MIDDLEWARE
# =====================================================

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    logger.info(
        "Incoming request | Method: %s | Path: %s",
        request.method,
        request.url.path,
    )

    try:
        response = await call_next(request)

        logger.info(
            "Request completed | Method: %s | Path: %s | Status: %s",
            request.method,
            request.url.path,
            response.status_code,
        )

        return response
    except Exception:
        logger.exception(
            "Request processing failed | Path: %s",
            request.url.path,
        )
        raise


# =====================================================
# VALIDATION ERROR HANDLER
# =====================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    logger.warning(
        "Validation failed | Path: %s | Error count: %s",
        request.url.path,
        len(exc.errors()),
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "loc": error["loc"],
                    "msg": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ]
        },
    )


# =====================================================
# GLOBAL UNEXPECTED ERROR HANDLER
# =====================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unexpected server error | Path: %s",
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": (
                "An unexpected server error occurred. "
                "Please try again later."
            )
        },
    )


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():
    logger.info("Home endpoint accessed")

    return {
        "message": "Card Dispute Triage API is running",
        "status": "healthy",
        "version": "2.0.0",
    }


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Health check successful")

        return {
            "status": "healthy",
            "service": "DisputeAI Backend",
            "database": "connected",
        }
    except Exception:
        logger.exception("Health check failed")

        raise HTTPException(
            status_code=503,
            detail="Backend or database is unavailable",
        )


# =====================================================
# CREATE DISPUTE WITH AI ANALYSIS
# =====================================================

@app.post("/api/disputes", status_code=201)
def create_dispute(
    dispute: DisputeCreate,
    db: Session = Depends(get_db),
):
    logger.info("New dispute submission received")

    # CHECK DUPLICATE TRANSACTION
    try:
        existing = (
            db.query(Dispute)
            .filter(Dispute.transaction_id == dispute.transaction_id)
            .first()
        )
    except Exception:
        logger.exception("Database query failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to verify transaction",
        )

    if existing:
        logger.warning(
            "Duplicate transaction detected | Dispute ID: %s",
            existing.dispute_id,
        )

        raise HTTPException(
            status_code=409,
            detail="This transaction already has a dispute",
        )

    # AI ANALYSIS WITH PROMETHEUS MONITORING
    ACTIVE_REQUESTS.inc()
    start_time = time.perf_counter()
    status = "success"

    try:
        ai_result = analyze_dispute(dispute)

        if ai_result.get("escalated"):
            HUMAN_ESCALATIONS.inc()

        logger.info(
            "AI analysis completed | Risk: %s | Priority: %s | Escalated: %s",
            ai_result["risk_score"],
            ai_result["priority"],
            ai_result["escalated"],
        )
    except Exception:
        status = "error"
        logger.exception("AI analysis failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to analyze dispute",
        )
    finally:
        VERIFICATION_DURATION.observe(time.perf_counter() - start_time)
        VERIFICATION_REQUESTS.labels(status=status).inc()
        ACTIVE_REQUESTS.dec()

    # CREATE DATABASE RECORD
    new_dispute = Dispute(
        dispute_id="DSP" + uuid.uuid4().hex[:8].upper(),
        customer_name=dispute.customer_name,
        transaction_id=dispute.transaction_id,
        amount=dispute.amount,
        transaction_type=dispute.transaction_type,
        transaction_date=str(dispute.transaction_date),
        reported_date=str(dispute.reported_date),
        fraud_description=dispute.fraud_description,
        otp_shared=dispute.otp_shared,
        fraud_type=ai_result["fraud_type"],
        risk_score=ai_result["risk_score"],
        priority=ai_result["priority"],
        escalated=ai_result["escalated"],
        recommendation=ai_result["recommendation"],
        status="Pending",
    )

    # SAVE DATABASE RECORD
    try:
        db.add(new_dispute)
        db.commit()
        db.refresh(new_dispute)

        logger.info(
            "Dispute created | ID: %s | Risk: %s",
            new_dispute.dispute_id,
            new_dispute.risk_score,
        )
    except Exception:
        db.rollback()
        logger.exception("Database save failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to save dispute",
        )

    return {
        "message": "Dispute successfully registered",
        "dispute_id": new_dispute.dispute_id,
        "status": new_dispute.status,
        "ai_analysis": ai_result,
    }


# =====================================================
# GET ALL DISPUTES
# =====================================================

@app.get("/api/disputes")
def get_disputes(db: Session = Depends(get_db)):
    try:
        disputes = db.query(Dispute).order_by(Dispute.id.desc()).all()

        logger.info(
            "Disputes retrieved | Count: %s",
            len(disputes),
        )

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
    except Exception:
        logger.exception("Failed to retrieve disputes")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve disputes",
        )


# =====================================================
# GET INDIVIDUAL DISPUTE
# =====================================================

@app.get("/api/disputes/{dispute_id}")
def get_dispute(
    dispute_id: str,
    db: Session = Depends(get_db),
):
    try:
        dispute_record = (
            db.query(Dispute)
            .filter(Dispute.dispute_id == dispute_id)
            .first()
        )

        if not dispute_record:
            logger.warning(
                "Dispute not found | ID: %s",
                dispute_id,
            )

            raise HTTPException(
                status_code=404,
                detail="Dispute not found",
            )

        logger.info(
            "Individual dispute retrieved | ID: %s",
            dispute_id,
        )

        return {
            "dispute_id": dispute_record.dispute_id,
            "customer_name": dispute_record.customer_name,
            "transaction_id": dispute_record.transaction_id,
            "amount": dispute_record.amount,
            "transaction_type": dispute_record.transaction_type,
            "transaction_date": dispute_record.transaction_date,
            "reported_date": dispute_record.reported_date,
            "fraud_description": dispute_record.fraud_description,
            "otp_shared": dispute_record.otp_shared,
            "fraud_type": dispute_record.fraud_type,
            "risk_score": dispute_record.risk_score,
            "priority": dispute_record.priority,
            "escalated": dispute_record.escalated,
            "recommendation": dispute_record.recommendation,
            "status": dispute_record.status,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to retrieve dispute | ID: %s",
            dispute_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve dispute",
        )


# =====================================================
# PROMETHEUS METRICS ENDPOINT
# =====================================================

@app.get("/metrics", include_in_schema=False)
def metrics():
    metrics_data, content_type = get_metrics()

    return Response(
        content=metrics_data,
        media_type=content_type,
    )
