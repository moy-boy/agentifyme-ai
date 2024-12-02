import os
import socket

import sentry_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from .semconv import SemanticAttributes


def get_resource_attributes() -> Resource:
    service_name = "agentifyme-pyworker"

    attributes = {
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_INSTANCE_ID: socket.gethostname(),
        ResourceAttributes.SERVICE_VERSION: "0.0.35",
        ResourceAttributes.PROCESS_PID: os.getpid(),
    }

    if os.getenv("AGENTIFYME_ORGANIZATION_ID"):
        attributes[SemanticAttributes.ORGANIZATION_ID] = os.getenv("AGENTIFYME_ORGANIZATION_ID")

    if os.getenv("AGENTIFYME_PROJECT_ID"):
        attributes[SemanticAttributes.PROJECT_ID] = os.getenv("AGENTIFYME_PROJECT_ID")

    if os.getenv("AGENTIFYME_WORKER_ID"):
        attributes[SemanticAttributes.WORKER_ID] = os.getenv("AGENTIFYME_WORKER_ID")

    if os.getenv("AGENTIFYME_DEPLOYMENT_ID"):
        attributes[SemanticAttributes.DEPLOYMENT_ID] = os.getenv("AGENTIFYME_DEPLOYMENT_ID")

    if os.getenv("AGENTIFYME_WORKER_ENDPOINT"):
        attributes[SemanticAttributes.WORKER_ENDPOINT] = os.getenv("AGENTIFYME_WORKER_ENDPOINT")

    if os.getenv("AGENTIFYME_ENV"):
        attributes[SemanticAttributes.SERVICE_ENV] = os.getenv("AGENTIFYME_ENV")

    resource = Resource(attributes=attributes)

    return resource


def configure_sentry(env: str, agentifyme_worker_version: str):
    sentry_dsn = os.getenv("AGENTIFYME_SENTRY_DSN")
    if not sentry_dsn:
        return

    sentry_sdk.init(
        dsn=sentry_dsn,
        release=f"agentifyme-worker@{agentifyme_worker_version}",
        environment=env,
        traces_sample_rate=1.0,
        server_name="agentifyme-worker",
        attach_stacktrace=True,
        enable_tracing=True,
    )
