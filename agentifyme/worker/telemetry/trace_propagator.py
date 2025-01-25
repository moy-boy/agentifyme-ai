
from opentelemetry.context import Context
from opentelemetry.trace import SpanContext, TraceFlags, get_current_span
from opentelemetry.trace.propagation.textmap import CarrierT, TextMapPropagator


class OTelTracePropagator(TextMapPropagator):
    """OpenTelemetry trace context propagator that follows the W3C Trace Context specification.
    Implements extraction and injection of trace context from/to carriers (e.g., HTTP headers).
    """

    TRACEPARENT_HEADER = "traceparent"
    TRACESTATE_HEADER = "tracestate"

    def extract(self, carrier: CarrierT, context: Context | None = None) -> Context:
        """Extract trace context from the carrier.

        Args:
            carrier: Carrier of propagated cross-cutting concerns. Usually HTTP headers.
            context: Context to be updated with the extracted trace context.

        Returns:
            New context with extracted trace information.

        """
        if context is None:
            context = Context()

        traceparent = carrier.get(self.TRACEPARENT_HEADER)
        if not traceparent:
            return context

        try:
            version, trace_id, span_id, trace_flags = self._parse_traceparent(traceparent)

            # Extract tracestate
            tracestate = carrier.get(self.TRACESTATE_HEADER, "")

            # Create span context
            span_context = SpanContext(
                trace_id=int(trace_id, 16), span_id=int(span_id, 16), trace_flags=TraceFlags(int(trace_flags, 16)), is_remote=True, trace_state=self._parse_tracestate(tracestate),
            )

            return context.with_span_context(span_context)

        except Exception:
            return context

    def inject(self, carrier: CarrierT, context: Context | None = None) -> None:
        """Inject trace context into the carrier.

        Args:
            carrier: Carrier of propagated cross-cutting concerns. Usually HTTP headers.
            context: Context containing the trace context to be injected.

        """
        span = get_current_span(context)
        if not span.is_recording():
            return

        span_context = span.get_span_context()
        if not span_context.is_valid:
            return

        # Format: 00-trace_id-span_id-trace_flags
        traceparent = f"00-{format(span_context.trace_id, '032x')}-{format(span_context.span_id, '016x')}-{format(span_context.trace_flags, '02x')}"
        carrier[self.TRACEPARENT_HEADER] = traceparent

        if span_context.trace_state:
            carrier[self.TRACESTATE_HEADER] = self._format_tracestate(span_context.trace_state)

    def _parse_traceparent(self, traceparent: str) -> tuple:
        """Parse traceparent header string into components."""
        parts = traceparent.split("-")
        if len(parts) != 4:
            raise ValueError("Invalid traceparent format")

        version, trace_id, span_id, trace_flags = parts

        if len(trace_id) != 32 or len(span_id) != 16:
            raise ValueError("Invalid trace_id or span_id length")

        return version, trace_id, span_id, trace_flags

    def _parse_tracestate(self, tracestate: str) -> dict[str, str]:
        """Parse tracestate header string into dictionary."""
        if not tracestate:
            return {}

        result = {}
        for pair in tracestate.split(","):
            try:
                key, value = pair.strip().split("=", 1)
                result[key.strip()] = value.strip()
            except ValueError:
                continue
        return result

    def _format_tracestate(self, tracestate: dict[str, str]) -> str:
        """Format tracestate dictionary into header string."""
        return ",".join(f"{k}={v}" for k, v in tracestate.items())

    @property
    def fields(self) -> set:
        """Return a set of keys that can be used to extract values from the carrier."""
        return {self.TRACEPARENT_HEADER, self.TRACESTATE_HEADER}
