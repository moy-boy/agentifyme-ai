from datetime import datetime
from typing import List

import pytest
from pydantic import BaseModel

from agentifyme.workflows import WorkflowConfig, workflow


class Email(BaseModel):
    from_: str
    to: List[str]
    cc: List[str]
    bcc: List[str]
    subject: str
    text_without_quote: str
    created_at: datetime


class EmailCategories(BaseModel):
    category: str
    confidence: float


@workflow(
    name="Classify email",
    description="Classify given email into actionable, informative or irrelevant categories",
)
def classify_email(email_message: Email) -> EmailCategories:
    # Dummy implementation for testing
    return EmailCategories(category="actionable", confidence=0.9)


@workflow(name="greet", description="Generate a greeting message.")
def greet(name: str) -> str:
    return f"Hello, {name}!"


def test_simple_workflow():
    workflow = WorkflowConfig._registry["greet"]
    result = workflow.run(name="Alice")
    assert result == {"output": "Hello, Alice!"}


def test_complex_workflow():
    workflow = WorkflowConfig._registry["Classify email"]
    input_data = {
        "email_message": {
            "from_": "sender@example.com",
            "to": ["recipient@example.com"],
            "cc": [],
            "bcc": [],
            "subject": "Test Email",
            "text_without_quote": "This is a test email.",
            "created_at": "2023-08-06T12:00:00",
        }
    }
    result = workflow.run(**input_data)
    assert result == {"category": "actionable", "confidence": 0.9}


def test_invalid_input():
    workflow = WorkflowConfig._registry["greet"]
    with pytest.raises(ValueError):
        workflow.run(invalid_param="Alice")


def test_missing_required_input():
    workflow = WorkflowConfig._registry["greet"]
    with pytest.raises(ValueError):
        workflow.run()


def test_extra_input_ignored():
    workflow = WorkflowConfig._registry["greet"]
    result = workflow.run(name="Bob", extra_param="Ignored")
    assert result == {"output": "Hello, Bob!"}
