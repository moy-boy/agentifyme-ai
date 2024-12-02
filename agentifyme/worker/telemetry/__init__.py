from loguru import logger as llogger

from .base import configure_sentry, get_resource_attributes
from .instrumentor import OTELInstrumentor
from .logger import configure_logger
from .tracer import configure_tracer


def setup_telemetry(otel_endpoint: str, agentifyme_env: str, agentifyme_worker_version: str):
    resource = get_resource_attributes()
    try:
        configure_sentry(agentifyme_env, agentifyme_worker_version)
        configure_logger(otel_endpoint, resource)
        configure_tracer(otel_endpoint, resource)
    except Exception as e:
        llogger.error(f"Error setting up OTEL: {e}")


def auto_instrument(project_dir: str):
    OTELInstrumentor().instrument(project_dir)


__all__ = ["setup_telemetry", "auto_instrument"]
