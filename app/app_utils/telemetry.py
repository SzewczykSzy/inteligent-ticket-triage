import logging
import os

from google.adk.cli.api_server import _setup_instrumentation_lib_if_installed
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def setup_telemetry() -> None:
    """Configure GenAI prompt/response logging and OpenTelemetry tracing locally."""
    # Keep full prompts/responses out of trace span attributes
    os.environ.setdefault("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "false")

    agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(agent_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    traces_file = os.path.join(logs_dir, "traces.json")

    # Configure Resource
    resource = Resource.create({"service.name": "inteligent-ticket-triage"})

    provider = TracerProvider(resource=resource)

    # 1. Local JSON File Exporter
    try:
        file_out = open(traces_file, "a")
        file_exporter = ConsoleSpanExporter(
            out=file_out, formatter=lambda span: span.to_json() + os.linesep
        )
        provider.add_span_processor(BatchSpanProcessor(file_exporter))
    except Exception as e:
        logging.error(f"Failed to setup file trace exporter: {e}")

    trace.set_tracer_provider(provider)

    # Set up GenAI SDK instrumentation
    _setup_instrumentation_lib_if_installed()
