# All credits to https://github.com/carolinecgilbert/opentelemetry-python-contrib/blob/1c92c51815aa3acfe31850ea055712bfbfc1f92c/handlers/opentelemetry_loguru/src/exporter.py

import os
import traceback
from time import time_ns

from loguru import logger
from opentelemetry._logs import SeverityNumber
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs._internal import LogRecord
from opentelemetry.sdk._logs._internal.export import (
    BatchLogRecordProcessor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import get_current_span
from opentelemetry.util.types import Attributes

from agentifyme.worker.telemetry.semconv import SemanticAttributes

_STD_TO_OTEL = {
    10: SeverityNumber.DEBUG,
    11: SeverityNumber.DEBUG2,
    12: SeverityNumber.DEBUG3,
    13: SeverityNumber.DEBUG4,
    14: SeverityNumber.DEBUG4,
    15: SeverityNumber.DEBUG4,
    16: SeverityNumber.DEBUG4,
    17: SeverityNumber.DEBUG4,
    18: SeverityNumber.DEBUG4,
    19: SeverityNumber.DEBUG4,
    20: SeverityNumber.INFO,
    21: SeverityNumber.INFO2,
    22: SeverityNumber.INFO3,
    23: SeverityNumber.INFO4,
    24: SeverityNumber.INFO4,
    25: SeverityNumber.INFO4,
    26: SeverityNumber.INFO4,
    27: SeverityNumber.INFO4,
    28: SeverityNumber.INFO4,
    29: SeverityNumber.INFO4,
    30: SeverityNumber.WARN,
    31: SeverityNumber.WARN2,
    32: SeverityNumber.WARN3,
    33: SeverityNumber.WARN4,
    34: SeverityNumber.WARN4,
    35: SeverityNumber.WARN4,
    36: SeverityNumber.WARN4,
    37: SeverityNumber.WARN4,
    38: SeverityNumber.WARN4,
    39: SeverityNumber.WARN4,
    40: SeverityNumber.ERROR,
    41: SeverityNumber.ERROR2,
    42: SeverityNumber.ERROR3,
    43: SeverityNumber.ERROR4,
    44: SeverityNumber.ERROR4,
    45: SeverityNumber.ERROR4,
    46: SeverityNumber.ERROR4,
    47: SeverityNumber.ERROR4,
    48: SeverityNumber.ERROR4,
    49: SeverityNumber.ERROR4,
    50: SeverityNumber.FATAL,
    51: SeverityNumber.FATAL2,
    52: SeverityNumber.FATAL3,
    53: SeverityNumber.FATAL4,
}

EXCLUDE_ATTR = (
    "elapsed",
    "exception",
    "extra",
    "file",
    "level",
    "process",
    "thread",
    "time",
)


class LoguruHandler:
    # this was largely inspired by the OpenTelemetry handler for stdlib `logging`:
    # https://github.com/open-telemetry/opentelemetry-python/blob/8f312c49a5c140c14d1829c66abfe4e859ad8fd7/opentelemetry-sdk/src/opentelemetry/sdk/_logs/_internal/__init__.py#L318

    def __init__(
        self,
        otel_endpoint: str,
        resource: Resource,
    ) -> None:
        logger_provider = LoggerProvider(resource=resource)

        # Set up the OTLP exporter
        exporter = OTLPLogExporter(endpoint=otel_endpoint, insecure=True)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter, max_export_batch_size=1))

        self._logger_provider = logger_provider
        self._logger = logger_provider.get_logger(__name__)

    def _get_attributes(self, record) -> Attributes:
        attributes = {key: value for key, value in record.items() if key not in EXCLUDE_ATTR}

        # Add standard code attributes for logs.
        attributes[SpanAttributes.CODE_FILEPATH] = record["file"].path  # This includes file and path -> (file, path)
        attributes[SpanAttributes.CODE_FUNCTION] = record["function"]
        attributes[SpanAttributes.CODE_LINENO] = record["line"]

        attributes["process_name"] = (record["process"]).name
        attributes["process_id"] = (record["process"]).id
        attributes["thread_name"] = (record["thread"]).name
        attributes["thread_id"] = (record["thread"]).id
        attributes["file"] = record["file"].name

        if os.getenv("AGENTIFYME_WORKER_ENDPOINT") is not None:
            attributes["endpoint"] = os.getenv("AGENTIFYME_WORKER_ENDPOINT")

        if os.getenv("AGENTIFYME_ORGANIZATION_ID") is not None:
            attributes[SemanticAttributes.ORGANIZATION_ID] = os.getenv("AGENTIFYME_ORGANIZATION_ID")

        if os.getenv("AGENTIFYME_PROJECT_ID") is not None:
            attributes[SemanticAttributes.PROJECT_ID] = os.getenv("AGENTIFYME_PROJECT_ID")

        if os.getenv("AGENTIFYME_DEPLOYMENT_ID") is not None:
            attributes[SemanticAttributes.DEPLOYMENT_ID] = os.getenv("AGENTIFYME_DEPLOYMENT_ID")

        if os.getenv("AGENTIFYME_WORKER_ID") is not None:
            attributes[SemanticAttributes.WORKER_ID] = os.getenv("AGENTIFYME_WORKER_ID")

        if record["exception"] is not None:
            exception_info = record["exception"]

            # Format exception type
            attributes[SpanAttributes.EXCEPTION_TYPE] = str(exception_info.type.__name__ if hasattr(exception_info.type, "__name__") else exception_info.type)

            # Format exception message
            attributes[SpanAttributes.EXCEPTION_MESSAGE] = str(exception_info.value)

            # Format traceback as a proper stack trace string
            if exception_info.traceback:
                tb_list = traceback.extract_tb(exception_info.traceback)
                formatted_tb = "\n".join(traceback.format_list(tb_list))
                attributes[SpanAttributes.EXCEPTION_STACKTRACE] = formatted_tb

        return attributes

    def _loguru_to_otel(self, levelno: int) -> SeverityNumber:
        if levelno < 10 or levelno == 25:
            return SeverityNumber.UNSPECIFIED

        if levelno > 53:
            return SeverityNumber.FATAL4

        return _STD_TO_OTEL[levelno]

    def _translate(self, record) -> LogRecord:
        # Timestamp
        timestamp = int((record["time"].timestamp()) * 1e9)

        # Observed timestamp
        observedTimestamp = time_ns()

        # Span context
        spanContext = get_current_span().get_span_context()

        # Setting the level name
        if record["level"].name == "WARNING":
            levelName = "WARN"
        elif record["level"].name == "TRACE" or record["level"].name == "SUCCESS":
            levelName = "NOTSET"
        else:
            levelName = record["level"].name

        # Severity number
        severityNumber = self._loguru_to_otel(int(record["level"].no))

        # Getting attributes
        attributes = self._get_attributes(record)

        return LogRecord(
            timestamp=timestamp,
            observed_timestamp=observedTimestamp,
            trace_id=spanContext.trace_id,
            span_id=spanContext.span_id,
            trace_flags=spanContext.trace_flags,
            severity_text=levelName,
            severity_number=severityNumber,
            body=record["message"],
            resource=self._logger.resource,
            attributes=attributes,
        )

    def sink(self, record) -> None:
        self._logger.emit(self._translate(record.record))


def configure_logger(otel_endpoint: str, resource: Resource):
    loguru_handler = LoguruHandler(otel_endpoint, resource)
    logger.add(loguru_handler.sink)
