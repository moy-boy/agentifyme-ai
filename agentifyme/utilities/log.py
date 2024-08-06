import json
import logging
import os

import httpx
import structlog
from dotenv import load_dotenv

load_dotenv(".env")
REMOTE_LOGGER_API_URL = os.getenv("REMOTE_LOGGER_API_URL")
REMOTE_LOGGER_API_TOKEN = os.getenv("REMOTE_LOGGER_API_TOKEN")
TRACING_API_URL = os.getenv("TRACING_API_URL")
TRACING_API_TOKEN = os.getenv("TRACING_API_TOKEN")


def send_events_to_remote_logger(event_dict):
    headers = {
        "Authorization": f"Bearer {REMOTE_LOGGER_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(REMOTE_LOGGER_API_URL, headers=headers, json=event_dict)
        if response.status_code != 202:
            print(f"Failed to send log event: {response.text}")
    except httpx.RequestError as e:
        print(f"An error occurred while sending log event: {str(e)}")


def remote_log_processor(logger, method_name, event_dict) -> dict:
    _event_dict = json.loads(event_dict)
    log_events = _event_dict.copy()

    _log = {}
    _log["timestamp"] = log_events.pop("timestamp")
    _log["level"] = log_events.pop("level")
    _log["event"] = log_events.pop("event")
    _log["data"] = json.dumps(log_events)
    send_events_to_remote_logger(_log)
    return _event_dict


def configure_logger():
    # processors = [
    #     structlog.contextvars.merge_contextvars,
    #     structlog.processors.add_log_level,
    #     structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    # ]

    # if REMOTE_LOGGER_API_URL and REMOTE_LOGGER_API_TOKEN:
    #     # FIXME: This is not working with async. Need to fix it.
    #     processors.append(structlog.processors.JSONRenderer())
    #     # processors.append(remote_log_processor)

    # processors.append(
    #     structlog.dev.ConsoleRenderer(),
    # )

    # structlog.configure(
    #     processors=processors,
    #     wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    #     context_class=dict,
    #     logger_factory=structlog.PrintLoggerFactory(),
    #     cache_logger_on_first_use=False,
    # )
    if not structlog.is_configured():
        structlog.reset_defaults()
        structlog.configure(
            processors=[structlog.processors.JSONRenderer()],
            logger_factory=structlog.ReturnLoggerFactory(),
        )
        print("Logger configured", structlog.is_configured())


def getLogger():
    configure_logger()
    log = structlog.get_logger()
    return log


def get_logger():
    configure_logger()
    log = structlog.get_logger()
    return log


def send_tracing_event(event_dict):
    headers = {
        "Authorization": f"Bearer {TRACING_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(TRACING_API_URL, headers=headers, json=event_dict)
        if response.status_code != 202:
            print(f"Failed to send log event: {response.text}")
    except httpx.RequestError as e:
        print(f"An error occurred while sending log event: {str(e)}")
