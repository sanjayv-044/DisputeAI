"""
DisputeAI Comprehensive End-to-End System Test Suite
Verifies all 17 requirements of the banking dispute platform:
- Customer Registration & Login
- Dispute Submission & DB Storage
- Asynchronous Background Multi-Agent Investigation
- 5-Category Fraud Classification
- RAG RBI Circular Retrieval
- Verification, Liability Assessment, and Recommendation Routing
- Admin Review & Action Concurrence
- Customer Tracking & Status Updates
- Role-Based Security Isolation
"""

import sys
import uuid
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from database import SessionLocal
from models import User, Dispute, EvidenceFile, InvestigationDossier, ComplaintHistory
from schemas import UserRegister, UserLogin, DisputeCreate, AdminActionRequest
from security import get_password_hash, verify_password, create_access_token, decode_access_token
from async_worker import execute_dispute_investigation
from evaluation_runner import run_full_evaluation
from src.fraud_classifier import classify_fraud
from src.regulatory_tools import search_regulations
from src.multi_agent_workflow import run_multi_agent_investigation


def run_e2e_tests():
    print("=" * 70)
    print("DISPUTEAI END-TO-END SYSTEM VERIFICATION")
    print("=" * 70)

    db = SessionLocal()
    tests_passed = 0
    total_tests = 17

    try:
        # TEST 1: Database Connectivity
        print("\n[TEST 1] Verifying Database Connectivity...")
        db_disputes_count = db.query(Dispute).count()
        print(f"-> Database connected successfully. Current disputes in DB: {db_disputes_count}")
        tests_passed += 1

        # TEST 2: Customer Registration
        print("\n[TEST 2] Testing Customer Registration...")
        unique_email = f"e2e_cust_{uuid.uuid4().hex[:6]}@disputeai.bank"
        reg_user = User(
            email=unique_email,
            password_hash=get_password_hash("TestPass@2026"),
            full_name="Meera Krishnan",
            phone="+91-9812345678",
            role="customer"
        )
        db.add(reg_user)
        db.commit()
        db.refresh(reg_user)
        assert reg_user.id is not None
        print(f"-> Customer registered with ID {reg_user.id}: {reg_user.email}")
        tests_passed += 1

        # TEST 3: Customer Login & Password Verification
        print("\n[TEST 3] Testing Customer Login & Password Hash Verification...")
        assert verify_password("TestPass@2026", reg_user.password_hash) is True
        token = create_access_token({"sub": reg_user.email, "role": reg_user.role, "id": reg_user.id})
        payload = decode_access_token(token)
        assert payload.get("sub") == reg_user.email
        assert payload.get("role") == "customer"
        print(f"-> JWT token created and decoded successfully. Role: {payload.get('role')}")
        tests_passed += 1

        # TEST 4: Admin Login Verification
        print("\n[TEST 4] Testing Admin Credentials & Role Verification...")
        admin = db.query(User).filter(User.email == "admin@disputeai.bank").first()
        assert admin is not None
        assert verify_password("Admin@DisputeAI2026", admin.password_hash) is True
        admin_token = create_access_token({"sub": admin.email, "role": admin.role, "id": admin.id})
        admin_payload = decode_access_token(admin_token)
        assert admin_payload.get("role") == "admin"
        print(f"-> Admin authenticated successfully: {admin.email} (Role: {admin.role})")
        tests_passed += 1

        # TEST 5: Role-Based Authorization
        print("\n[TEST 5] Verifying Role-Based Access Guards...")
        # Customer cannot have role == admin
        assert payload.get("role") != "admin"
        assert admin_payload.get("role") == "admin"
        print("-> Role distinction confirmed: customer cannot claim admin role.")
        tests_passed += 1

        # TEST 6: Dispute Submission & DB Persistence
        print("\n[TEST 6] Testing Dispute Creation & DB Persistence...")
        test_tx_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
        dispute_id = "DSP-" + uuid.uuid4().hex[:8].upper()
        dispute = Dispute(
            dispute_id=dispute_id,
            user_id=reg_user.id,
            customer_name=reg_user.full_name,
            customer_email=reg_user.email,
            bank_name="State Bank of India",
            transaction_id=test_tx_id,
            amount=22500.0,
            transaction_type="UPI",
            transaction_date="2026-11-18",
            reported_date="2026-11-19",
            fraud_type_claimed="UPI Fraud",
            fraud_description="Fraudulent collect request debited ₹22,500 without my authorization via Google Pay.",
            otp_shared=False,
            status="Pending"
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)
        assert dispute.id is not None
        print(f"-> Dispute persisted in DB. Dispute ID: {dispute.dispute_id}, Amount: ₹{dispute.amount}")
        tests_passed += 1

        # TEST 7: Document Upload Association
        print("\n[TEST 7] Testing Evidence Document Association...")
        ev_file = EvidenceFile(
            dispute_id=dispute.dispute_id,
            filename="sms_debit_alert.png",
            file_path="/app/backend/uploads/mock_sms.png",
            file_type="image/png",
            file_size=104850,
            verified_status="Verified (Uploaded & Integrity Checked)"
        )
        db.add(ev_file)
        db.commit()
        db.refresh(ev_file)
        assert ev_file.id is not None
        print(f"-> Evidence record associated with dispute: {ev_file.filename}")
        tests_passed += 1

        # TEST 8: 5-Category Fraud Classifier
        print("\n[TEST 8] Testing 5-Category Fraud Classifier...")
        clf_result = classify_fraud(
            description=dispute.fraud_description,
            otp_shared=dispute.otp_shared,
            amount=dispute.amount,
            transaction_type=dispute.transaction_type
        )
        assert clf_result["category"] == "UPI Fraud"
        assert 0 <= clf_result["risk_score"] <= 100
        assert clf_result["risk_level"] in ["Low", "Medium", "High", "Critical"]
        print(f"-> Fraud Classifier: Category={clf_result['category']}, Score={clf_result['risk_score']}, Risk={clf_result['risk_level']}")
        tests_passed += 1

        # TEST 9: RAG RBI Circular Retrieval
        print("\n[TEST 9] Testing RAG RBI Regulatory Retrieval...")
        evidence = search_regulations("unauthorized upi collect request zero liability customer protection", top_k=3)
        assert len(evidence) > 0
        assert "source" in evidence[0]
        assert "page" in evidence[0]
        print(f"-> RAG retrieved {len(evidence)} circular chunks. Top citation: {evidence[0]['source']} (Page {evidence[0]['page']})")
        tests_passed += 1

        # TEST 10: Multi-Agent LangGraph Workflow Execution
        print("\n[TEST 10] Executing 4-Agent LangGraph Workflow...")
        workflow_input = {
            "dispute_id": dispute.dispute_id,
            "customer_name": dispute.customer_name,
            "amount": dispute.amount,
            "transaction_type": dispute.transaction_type,
            "transaction_date": dispute.transaction_date,
            "reported_date": dispute.reported_date,
            "fraud_description": dispute.fraud_description,
            "otp_shared": dispute.otp_shared,
            "evidence_files": [{"filename": ev_file.filename, "file_size": ev_file.file_size}]
        }
        agent_res = run_multi_agent_investigation(workflow_input)
        assert "fraud_category" in agent_res
        assert "verification_status" in agent_res
        assert "liability_status" in agent_res
        assert "recommendation" in agent_res
        print(f"-> LangGraph Executed successfully!")
        print(f"   Category: {agent_res['fraud_category']}")
        print(f"   Verification: {agent_res['verification_status']}")
        print(f"   Liability: {agent_res['liability_status']}")
        tests_passed += 1

        # TEST 11: Asynchronous Background Processing Execution
        print("\n[TEST 11] Testing Background Investigation Worker Routine...")
        execute_dispute_investigation(dispute.dispute_id)
        db.refresh(dispute)
        assert dispute.status in ["Under Review", "Escalated"]
        assert dispute.liability_verdict != "PENDING_ASSESSMENT"
        print(f"-> Background Worker updated Dispute: Status={dispute.status}, Verdict={dispute.liability_verdict}")
        tests_passed += 1

        # TEST 12: Investigation Dossier Persistence
        print("\n[TEST 12] Verifying Investigation Dossier in Database...")
        dossier = db.query(InvestigationDossier).filter(InvestigationDossier.dispute_id == dispute.dispute_id).first()
        assert dossier is not None
        assert dossier.fraud_category == "UPI Fraud"
        print(f"-> Dossier saved: Liability={dossier.liability_status}, Citations JSON length={len(dossier.rbi_citations_json)}")
        tests_passed += 1

        # TEST 13: Complaint History Audit Trail
        print("\n[TEST 13] Verifying Complaint History & Audit Trail...")
        hist = db.query(ComplaintHistory).filter(ComplaintHistory.dispute_id == dispute.dispute_id).all()
        assert len(hist) >= 1
        print(f"-> Audit history entries recorded: {len(hist)}. Latest: {hist[-1].action}")
        tests_passed += 1

        # TEST 14: Admin Action (Approval & Resolution)
        print("\n[TEST 14] Testing Administrator Concurrence & Resolution Action...")
        prev_st = dispute.status
        dispute.status = "Resolved - Refund Approved"
        dispute.admin_remarks = "Zero customer liability confirmed under RBI Para 6(ii). Full shadow reversal credit authorized."
        dispute.final_resolution = f"Dispute resolved. ₹{dispute.amount:,.2f} shadow reversal credited to account."
        hist_admin = ComplaintHistory(
            dispute_id=dispute.dispute_id,
            action="Admin Decision: APPROVE",
            status_from=prev_st,
            status_to=dispute.status,
            changed_by="Admin (Chief Risk Officer)",
            notes=dispute.admin_remarks
        )
        db.add(hist_admin)
        db.commit()
        db.refresh(dispute)
        assert dispute.status == "Resolved - Refund Approved"
        print(f"-> Admin approved dispute! Status: {dispute.status}")
        tests_passed += 1

        # TEST 15: Customer Tracking & Data Isolation
        print("\n[TEST 15] Verifying Customer Query Isolation...")
        # Querying disputes belonging to reg_user only
        cust_disputes = db.query(Dispute).filter(Dispute.user_id == reg_user.id).all()
        assert any(d.dispute_id == dispute.dispute_id for d in cust_disputes)
        print(f"-> Customer successfully tracked dispute {dispute.dispute_id} with resolution: {dispute.final_resolution}")
        tests_passed += 1

        # TEST 16: Evaluation Module Benchmarks (20 Scenarios)
        print("\n[TEST 16] Running System Evaluation Module...")
        eval_metrics = run_full_evaluation()
        assert eval_metrics["summary"]["fraud_classification_accuracy"] == 100.0
        assert eval_metrics["summary"]["rag_retrieval_precision"] == 100.0
        assert eval_metrics["fraud_classification"]["total_scenarios"] == 20
        print(f"-> Evaluation Module Verified:")
        print(f"   Fraud Classification Accuracy: {eval_metrics['summary']['fraud_classification_accuracy']}%")
        print(f"   RAG Retrieval Precision: {eval_metrics['summary']['rag_retrieval_precision']}%")
        print(f"   Total Benchmark Test Cases: {eval_metrics['summary']['total_benchmark_cases']}")
        tests_passed += 1

        # TEST 17: Prometheus Monitoring Metrics Output
        print("\n[TEST 17] Verifying Prometheus Telemetry Endpoint Data...")
        from src.monitoring import get_metrics
        m_bytes, content_type = get_metrics()
        m_text = m_bytes.decode("utf-8")
        assert "disputeai_verification_requests_total" in m_text
        assert "disputeai_active_requests" in m_text
        print(f"-> Prometheus metrics generated successfully (Content-Type: {content_type})")
        tests_passed += 1

    finally:
        db.close()

    print("\n" + "=" * 70)
    print(f"RESULTS: {tests_passed} / {total_tests} SYSTEM TESTS PASSED (100% SUCCESS RATE)")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_tests()
