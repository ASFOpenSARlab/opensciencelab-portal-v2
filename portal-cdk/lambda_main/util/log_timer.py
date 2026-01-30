import time
from contextlib import contextmanager

from aws_lambda_powertools import Logger

logger = Logger(child=True)


@contextmanager
def measure_time(service, action) -> None:
    start_time = time.perf_counter()
    yield
    elapsed_time_ms = round((time.perf_counter() - start_time) * 1000)

    # Using the 'extra' parameter
    additional_attributes = {
        "times_ms": elapsed_time_ms,
        "service": service,
        "action": action,
    }
    logger.info(
        f"External service timing: {service}/{action}: {elapsed_time_ms}",
        extra=additional_attributes,
    )
