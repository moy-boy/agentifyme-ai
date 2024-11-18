import os

from loguru import logger as llogger

from .base import configure_sentry, get_resource_attributes
from .logger import configure_logger
from .tracer import configure_tracer


def setup_telemetry(env: str, agentifyme_worker_version: str):
    otel_endpoint = os.getenv("AGENTIFYME_OTEL_ENDPOINT")
    if otel_endpoint == "" or otel_endpoint is None:
        llogger.warning("OTEL_ENDPOINT not set. Skipping OTEL logging")
        return

    resource = get_resource_attributes()
    try:
        llogger.info(
            f"Setting up Sentry with env {env} and version {agentifyme_worker_version}"
        )
        configure_sentry(env, agentifyme_worker_version)
        llogger.info(f"Setting up Logger with OTEL endpoint {otel_endpoint}")
        configure_logger(otel_endpoint, resource)
        llogger.info(f"Setting up Tracer with OTEL endpoint {otel_endpoint}")
        configure_tracer(otel_endpoint, resource)
        llogger.info("OTEL setup complete")
    except Exception as e:
        llogger.error(f"Error setting up OTEL: {e}")


__all__ = ["setup_telemetry"]
