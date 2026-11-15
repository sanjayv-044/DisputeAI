import time
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Total verification requests
VERIFICATION_REQUESTS = Counter(
    "disputeai_verification_requests_total",
    "Total number of verification requests",
    ["status"]
)

# Verification processing time
VERIFICATION_DURATION = Histogram(
    "disputeai_verification_duration_seconds",
    "Time taken to process verification requests"
)

# Human escalation count
HUMAN_ESCALATIONS = Counter(
    "disputeai_human_escalations_total",
    "Total number of cases escalated for human review"
)

# Current active requests
ACTIVE_REQUESTS = Gauge(
    "disputeai_active_requests",
    "Number of currently active verification requests"
)


def monitor_verification(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ACTIVE_REQUESTS.inc()
        start = time.perf_counter()
        status = "success"

        try:
            result = func(*args, **kwargs)

            if isinstance(result, dict):
                if result.get("escalation_required") or result.get("human_escalation"):
                    HUMAN_ESCALATIONS.inc()

            return result

        except Exception:
            status = "error"
            raise

        finally:
            VERIFICATION_DURATION.observe(time.perf_counter() - start)
            VERIFICATION_REQUESTS.labels(status=status).inc()
            ACTIVE_REQUESTS.dec()

    return wrapper


def get_metrics():
    return generate_latest(), CONTENT_TYPE_LATEST
