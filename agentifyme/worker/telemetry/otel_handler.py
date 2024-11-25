import ast
import logging

logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
import os

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.resources import Resource


class OTELHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.log_attributes = dict(self._get_attributes())
        self.handler = self._create_handler()

    def _get_attributes(self) -> dict:
        _attributes = {}
        _attributes["project"] = os.getenv("AGENTIFYME_PROJECT_ID")
        _attributes["organization"] = os.getenv("AGENTIFYME_ORGANIZATION_ID")
        _attributes["deployment"] = os.getenv("AGENTIFYME_DEPLOYMENT_ID")
        _attributes["replica"] = os.getenv("AGENTIFYME_REPLICA_ID")
        return _attributes

    def _create_handler(self):

        resource = Resource.create(
            {
                "service.name": "worker",
                "service.namespace": "agentifyme",
                "deployment.environment": "agentifyme-dev",
            }
        )
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)

        endpoint = os.getenv("AGENTIFYME_OTEL_ENDPOINT", "54.81.55.185:4317")
        exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)
        logger_provider.add_log_record_processor(SimpleLogRecordProcessor(exporter))

        # Attach OTLP handler to root logger
        handler = LoggingHandler(logger_provider=logger_provider)

        return handler

    def _parse_single_quoted_dict(self, s):
        # Replace single quotes with double quotes, but not for 'true' and 'false'
        s = s.replace("'", '"').replace('"true"', "true").replace('"false"', "false")

        # Use ast.literal_eval to safely evaluate the string as a Python literal
        return ast.literal_eval(s)

    def _str_to_log_level(self, level_str):
        """
        Convert a string representation of a logging level to its corresponding integer value.

        :param level_str: A string representing the logging level (case-insensitive)
        :return: The corresponding integer logging level
        :raises ValueError: If the input string doesn't match a valid logging level
        """
        level_str = level_str.upper()
        level_map = {
            "CRITICAL": logging.CRITICAL,
            "FATAL": logging.FATAL,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "WARN": logging.WARN,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
            "NOTSET": logging.NOTSET,
        }

        if level_str in level_map:
            return level_map[level_str]
        else:
            raise ValueError(f"Invalid logging level: {level_str}")

    def emit(self, record: logging.LogRecord):

        print(">>", record.getMessage())
        # if not message.startswith("{"):
        #     return

        # message = self._parse_single_quoted_dict(message)

        # if isinstance(message, dict):
        #     msg = message.pop("event", "")
        #     level = self._str_to_log_level(message.pop("level", "info"))
        #     func_name = "function_name"

        #     _log_attributes = self.log_attributes.copy()
        #     _log_attributes.update(message)
        #     _record = logging.LogRecord(
        #         name="log",
        #         level=level,
        #         msg=msg,
        #         pathname="agentifyme-py-sdk",
        #         lineno=10,
        #         args=_log_attributes,
        #         exc_info=None,
        #         func=func_name,
        #     )

        #     self.handler.emit(_record)
