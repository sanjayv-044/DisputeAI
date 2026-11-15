from src.monitoring import monitor_verification, get_metrics

@monitor_verification
def sample_verification():
    return {"status": "completed"}

sample_verification()

metrics = get_metrics()[0].decode()

assert "disputeai_verification_requests_total" in metrics
assert "disputeai_verification_duration_seconds_count 1.0" in metrics

print("Monitoring test passed!")
print("Verification request recorded.")
print("Response time recorded.")
