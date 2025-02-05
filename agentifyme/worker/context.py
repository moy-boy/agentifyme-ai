from contextvars import ContextVar

from loguru import logger

from agentifyme.worker.telemetry.semconv import SemanticAttributes

workflow_run_id = ContextVar[str | None]("workflow_run_id", default=None)
workflow_name = ContextVar[str | None]("workflow_name", default=None)
trace_id = ContextVar[str | None]("trace_id", default=None)


def context_injector(record):
    """Inject workflow run ID into the record"""
    run_id = workflow_run_id.get()
    if run_id is not None:
        record["extra"][SemanticAttributes.WORKFLOW_RUN_ID] = run_id

    name = workflow_name.get()
    if name is not None:
        record["extra"][SemanticAttributes.WORKFLOW_NAME] = name

    tid = trace_id.get()
    if tid is not None:
        record["extra"]["trace_id"] = tid


logger.configure(patcher=context_injector)
