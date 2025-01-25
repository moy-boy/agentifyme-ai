from loguru import logger as llogger

from agentifyme.worker.callback import CallbackHandler

from .base import configure_sentry, get_resource_attributes
from .instrumentor import OTELInstrumentor
from .language_model import auto_instrument_language_models
from .logger import configure_logger
from .tracer import configure_tracer


def setup_telemetry(otel_endpoint: str, agentifyme_env: str, agentifyme_worker_version: str):
    resource = get_resource_attributes()
    llogger.info(f"Setting up telemetry with resource: {resource}")
    try:
        configure_sentry(agentifyme_env, agentifyme_worker_version)
        configure_logger(otel_endpoint, resource)
        configure_tracer(otel_endpoint, resource)
    except Exception as e:
        llogger.error(f"Error setting up OTEL: {e}")


def auto_instrument(project_dir: str, callback_handler: CallbackHandler):
    OTELInstrumentor().instrument(project_dir, callback_handler)
    auto_instrument_language_models(callback_handler)


__all__ = ["auto_instrument", "setup_telemetry"]
