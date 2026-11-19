from src.monitoring import (
    monitor_verification,
    get_metrics
)


def test_monitoring_metrics():
    @monitor_verification
    def normal_verification():
        return {"status": "completed"}

    @monitor_verification
    def escalated_verification():
        return {"escalation_required": True}

    # Execute two verification requests
    normal_verification()
    escalated_verification()

    # Collect Prometheus metrics
    metrics = get_metrics()[0].decode("utf-8")

    # Verify successful requests
    assert (
        'disputeai_verification_requests_total{status="success"} 2.0'
        in metrics
    )

    # Verify request processing duration
    assert (
        "disputeai_verification_duration_seconds_count 2.0"
        in metrics
    )

    # Verify human escalation
    assert (
        "disputeai_human_escalations_total 1.0"
        in metrics
    )

    # Verify no requests remain active
    assert (
        "disputeai_active_requests 0.0"
        in metrics
    )