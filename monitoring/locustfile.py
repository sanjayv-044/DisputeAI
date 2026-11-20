"""
DisputeAI Locust Load Testing Suite
Simulates realistic banking customer & administrator workloads:
1. Customer Registration & Login
2. Dispute Submission (with amount, dates, OTP flags, description)
3. Status Tracking & AI Investigation Polling
4. Admin Dashboard Analytics & Case Review
"""

import uuid
import random
from datetime import date, timedelta
from locust import HttpUser, task, between


class DisputeAIUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Register and authenticate user session."""
        self.email = f"loadtest_{uuid.uuid4().hex[:6]}@disputeai.bank"
        self.password = "SecurePassword@123"
        self.token = None
        self.role = "customer"

        # Register
        reg_resp = self.client.post("/api/auth/register", json={
            "email": self.email,
            "password": self.password,
            "full_name": "Performance Test User",
            "phone": "+91-9876543210",
            "role": "customer"
        })

        if reg_resp.status_code == 201:
            data = reg_resp.json()
            self.token = data.get("access_token")
        else:
            # Fallback to demo login
            login_resp = self.client.post("/api/auth/login", json={
                "email": "customer@disputeai.bank",
                "password": "Customer@DisputeAI2026"
            })
            if login_resp.status_code == 200:
                self.token = login_resp.json().get("access_token")

    @task(3)
    def submit_banking_dispute(self):
        """Simulate dispute submission by a customer."""
        if not self.token:
            return

        tx_types = ["UPI", "Card", "Internet Banking"]
        chosen_type = random.choice(tx_types)
        amount = random.choice([1500.0, 4800.0, 12500.0, 35000.0, 85000.0])
        otp_shared = random.choice([False, False, True])

        descriptions = [
            "Unauthorized UPI collect request was debited without my permission.",
            "My debit card was cloned at an ATM and money was debited.",
            "Phishing caller impersonated my bank manager and money was transferred.",
            "Unknown transaction appeared on my statement while traveling.",
            "Payment debited twice for one POS transaction at merchant."
        ]

        today = date.today()
        tx_date = today - timedelta(days=random.randint(1, 5))

        payload = {
            "customer_name": "Performance Test User",
            "customer_email": self.email,
            "bank_name": "State Bank of India",
            "transaction_id": f"TXN{uuid.uuid4().hex[:10].upper()}",
            "amount": amount,
            "transaction_type": chosen_type,
            "transaction_date": str(tx_date),
            "reported_date": str(today),
            "fraud_type_claimed": "Unknown",
            "fraud_description": random.choice(descriptions),
            "otp_shared": otp_shared
        }

        headers = {"Authorization": f"Bearer {self.token}"}
        resp = self.client.post("/api/customer/disputes", json=payload, headers=headers)
        if resp.status_code == 201:
            data = resp.json()
            self.last_dispute_id = data.get("dispute_id")

    @task(4)
    def check_customer_complaints(self):
        """Customer tracks previously submitted complaints."""
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/customer/disputes", headers=headers)

    @task(2)
    def check_system_health(self):
        """Health check endpoint polling."""
        self.client.get("/health")


class AdminUser(HttpUser):
    wait_time = between(2, 5)

    def on_start(self):
        """Authenticate as System Administrator."""
        resp = self.client.post("/api/auth/login", json={
            "email": "admin@disputeai.bank",
            "password": "Admin@DisputeAI2026"
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")
        else:
            self.token = None

    @task(3)
    def view_admin_analytics(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/admin/analytics", headers=headers)

    @task(3)
    def view_all_complaints(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/admin/disputes", headers=headers)

    @task(1)
    def view_system_monitoring(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/admin/monitoring", headers=headers)
