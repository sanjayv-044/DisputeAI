
import time
from src.regulatory_tools import search_regulations


def reliable_search(question, top_k=5, max_retries=3, timeout_seconds=20):
    """
    Retry regulatory retrieval when an error occurs.
    Stop attempting after the configured timeout.
    """

    for attempt in range(1, max_retries + 1):
        start_time = time.monotonic()

        try:
            results = search_regulations(question, top_k)

            elapsed = time.monotonic() - start_time

            if elapsed > timeout_seconds:
                raise TimeoutError("Regulatory retrieval timed out.")

            return results

        except Exception as error:
            print(f"Attempt {attempt} failed: {error}")

            if attempt == max_retries:
                return {
                    "error": "Regulatory retrieval failed after retries.",
                    "details": str(error)
                }

            time.sleep(1)


print("Reliable retrieval module created successfully!")
