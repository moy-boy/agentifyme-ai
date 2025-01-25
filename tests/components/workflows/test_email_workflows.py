from datetime import datetime

import pytest
from pydantic import BaseModel

from agentifyme.components.workflow import WorkflowConfig, workflow
from agentifyme.errors import AgentifyMeError


class Email(BaseModel):
    from_: str
    to: list[str]
    cc: list[str]
    bcc: list[str]
    subject: str
    text_without_quote: str
    created_at: datetime


class EmailCategories(BaseModel):
    category: str
    confidence: float


class EmailContent(BaseModel):
    content: str


@workflow(name="greet", description="Generate a greeting message.")
def greet(name: str) -> str:
    return f"Hello, {name}!"


@workflow(
    name="classify-email",
    description="Classify email into actionable, informative or irrelevant categories",
)
def classify_email(email_message: Email) -> EmailCategories:
    return EmailCategories(category="actionable", confidence=0.9)


@workflow(
    name="extract-email-content",
    description="Extract the content of the email",
)
def email_content(email_message: Email) -> EmailContent:
    _email = f"""
    From: {email_message.from_}
    To: {email_message.to}
    Subject: {email_message.subject}
    Text: {email_message.text_without_quote}
    """
    return EmailContent(content=_email)


def test_simple_workflow():
    all_workflows = WorkflowConfig.get_all()
    assert "greet" in all_workflows
    assert "classify-email" in all_workflows


def test_complex_workflow():
    _workflow = WorkflowConfig.get("classify-email")
    input_data = {
        "email_message": Email(
            from_="sender@example.com",
            to=["recipient@example.com"],
            cc=[],
            bcc=[],
            subject="Test Email",
            text_without_quote="This is a test email.",
            created_at=datetime(2023, 8, 6, 12, 0, 0),
        )
    }
    result = email_content(**input_data)
    assert "This is a test email." in result.content
    assert "sender@example.com" in result.content
    assert "recipient@example.com" in result.content
    assert "Test Email" in result.content


def test_invalid_input():
    _workflow = WorkflowConfig.get("greet")
    with pytest.raises(AgentifyMeError) as exc_info:
        _workflow.run(invalid_param="Alice")

    error = exc_info.value
    assert error.context.component_type == "workflow"
    assert error.context.component_id == "greet"
    assert "invalid_param" in error.execution_state
    print(error)
