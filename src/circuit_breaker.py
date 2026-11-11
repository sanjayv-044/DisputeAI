
import time


class CircuitBreaker:

    def __init__(self, failure_threshold=3, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def call(self, function, *args, **kwargs):

        if self.state == "OPEN":
            elapsed = time.monotonic() - self.last_failure_time

            if elapsed < self.recovery_timeout:
                raise RuntimeError(
                    "Circuit is OPEN. Request temporarily blocked."
                )

            self.state = "HALF-OPEN"

        try:
            result = function(*args, **kwargs)

            self.failure_count = 0
            self.state = "CLOSED"

            return result

        except Exception:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise


print("Circuit breaker module created successfully!")
