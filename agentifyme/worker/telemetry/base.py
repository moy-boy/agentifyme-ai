import os
import socket

import sentry_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


def get_resource_attributes() -> Resource:
    service_name = "agentifyme-pyworker"

    attributes = {
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_INSTANCE_ID: socket.gethostname(),
        ResourceAttributes.SERVICE_VERSION: "0.0.35",
        ResourceAttributes.PROCESS_PID: os.getpid(),
    }

    if os.getenv("AGENTIFYME_ORGANIZATION_ID"):
        attributes["agentifyme.organization.id"] = os.getenv(
            "AGENTIFYME_ORGANIZATION_ID"
        )

    if os.getenv("AGENTIFYME_PROJECT_ID"):
        attributes["agentifyme.project.id"] = os.getenv("AGENTIFYME_PROJECT_ID")

    if os.getenv("AGENTIFYME_REPLICA_ID"):
        attributes["agentifyme.replica.id"] = os.getenv("AGENTIFYME_REPLICA_ID")

    if os.getenv("AGENTIFYME_DEPLOYMENT_ID"):
        attributes["agentifyme.deployment.id"] = os.getenv("AGENTIFYME_DEPLOYMENT_ID")

    if os.getenv("AGENTIFYME_WORKER_ENDPOINT"):
        attributes["agentifyme.worker.endpoint"] = os.getenv(
            "AGENTIFYME_WORKER_ENDPOINT"
        )

    if os.getenv("AGENTIFYME_ENV"):
        attributes["agentifyme.env"] = os.getenv("AGENTIFYME_ENV")

    resource = Resource(attributes=attributes)

    return resource


def configure_sentry(env: str, agentifyme_worker_version: str):
    if env != "agentifyme-dev":
        sentry_sdk.init(
            dsn="https://ee07fb8a706601880d3eb28c3fac473c@sentry.protoml.xyz/8",
            release=f"agentifyme-worker@{agentifyme_worker_version}",
            environment=env,
            traces_sample_rate=1.0,
            server_name="agentifyme-worker",
            attach_stacktrace=True,
            enable_tracing=True,
        )
