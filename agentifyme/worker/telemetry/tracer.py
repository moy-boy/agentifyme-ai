from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import context, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.processor.baggage import ALLOW_ALL_BAGGAGE_KEYS, BaggageSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def add_trace_info(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span:
        ctx = context.get_current()
        trace_id = trace.get_current_span(ctx).get_span_context().trace_id
        span_id = trace.get_current_span(ctx).get_span_context().span_id
        event_dict["trace_id"] = f"{trace_id:032x}"
        event_dict["span_id"] = f"{span_id:016x}"
    return event_dict


def configure_tracer(otel_endpoint: str, resource: Resource):
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BaggageSpanProcessor(ALLOW_ALL_BAGGAGE_KEYS))
    trace.set_tracer_provider(tracer_provider)
    otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
