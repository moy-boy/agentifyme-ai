# AgentifyMe AI

AgentifyMe AI is a Python framework for building agentic workflows and LLM-powered applications. It helps developers define reusable units of work, register them as tasks or workflows, connect them to language models, and execute them through a consistent runtime.

The project is designed for applications that need more structure than a single prompt call. It provides decorators for declaring tasks and workflows, metadata extraction for inputs and outputs, language model abstractions, prompt utilities, worker execution, telemetry, and supporting integrations for embeddings and vector stores.

## Features

- Decorator-based task and workflow definitions
- Sync and async execution support
- Automatic metadata collection from Python function signatures
- Pydantic-friendly input and output handling
- Language model interfaces for OpenAI, Anthropic, Cohere, Groq, and Together
- Prompt, caching, logging, and JSON utilities
- Worker runtime components for remote workflow execution
- OpenTelemetry-based tracing and runtime observability
- Optional vector store support for Qdrant and Pinecone

## Installation

Install from a local checkout:

```bash
pip install .
```

Install with optional worker runtime dependencies:

```bash
pip install ".[worker]"
```

Install with optional provider or vector store integrations:

```bash
pip install ".[groq]"
pip install ".[together]"
pip install ".[qdrant]"
pip install ".[pinecone]"
```

## Basic Usage

Define a task with the `@task` decorator:

```python
from agentifyme import task


@task(name="summarize_topic", description="Create a short summary for a topic.")
def summarize_topic(topic: str) -> str:
    return f"Summary for {topic}"


result = summarize_topic("agentic workflows")
```

Define a workflow with the `@workflow` decorator:

```python
from agentifyme import workflow


@workflow(name="research_workflow", description="Run a simple research workflow.")
def research_workflow(topic: str) -> dict:
    return {
        "topic": topic,
        "status": "completed",
    }


output = research_workflow("LLM agents")
```

Both tasks and workflows are registered with metadata about their names, descriptions, inputs, outputs, and async behavior. That metadata can be used by runtime components to discover and execute available workflows.

## Project Structure

```text
agentifyme/
  components/       Task and workflow primitives
  ml/               Language model and embedding abstractions
  tasks/            Built-in structured data extraction tasks
  document_stores/  Vector store interfaces and integrations
  worker/           Worker runtime, callbacks, telemetry, and gRPC support
  utilities/        Shared helpers for JSON, environment, modules, and timing
```

## Core Concepts

Tasks are individual callable units. They are useful for small pieces of logic such as extracting data, calling a model, transforming a response, or validating output.

Workflows are higher-level callable units. They can compose multiple steps, expose a typed interface, and optionally carry schedule metadata.

Language model providers are accessed through common interfaces so application code can work with model responses, tool calls, streaming output, and usage information in a consistent way.

The worker runtime is intended for deployed execution. It can discover registered workflows, receive execution commands, deserialize inputs, run workflow functions, serialize outputs, and emit telemetry.

## Development

Install development dependencies with `uv` or your preferred Python environment manager, then run the test suite:

```bash
uv sync
uv run pytest
```

The package targets Python 3.11 and newer.
