from datetime import datetime
from typing import List

import pytest
from pydantic import BaseModel

from agentifyme.utilities.func_utils import execute_function


# Assuming the same Email and EmailCategories classes as before
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
    score: int
    explanation: str
    tags: List[str]


# Test data
valid_email_json = {
    "email_message": {
        "from_": "sender@example.com",
        "to": ["recipient@example.com"],
        "cc": [],
        "bcc": [],
        "subject": "Important Meeting",
        "text_without_quote": "Please attend the meeting tomorrow at 2 PM.",
        "created_at": "2023-08-07T10:00:00Z",
    }
}

invalid_email_json = {
    "email_message": {
        "from_": "sender@example.com",
        "to": ["recipient@example.com"],
        "cc": [],
        "bcc": [],
        "subject": "Important Meeting",
        "text_without_quote": "Please attend the meeting tomorrow at 2 PM.",
        # Missing created_at field
    }
}

missing_param_json = {}


async def async_get_email_message(email_message: Email) -> str:
    return email_message.text_without_quote


async def async_mock_classify_email(email_message: Email) -> EmailCategories:
    return EmailCategories(
        category="Informative",
        score=80,
        explanation="The email contains information about a meeting.",
        tags=["meeting", "schedule"],
    )


def test_async_email_message():
    result = execute_function(async_get_email_message, valid_email_json)
    assert isinstance(result, str)
    assert result == "Please attend the meeting tomorrow at 2 PM."


def test_async_valid_input():
    result = execute_function(async_mock_classify_email, valid_email_json)
    assert isinstance(result, EmailCategories)
    assert result.category == "Informative"
    assert result.score == 80
    assert result.explanation == "The email contains information about a meeting."
    assert result.tags == ["meeting", "schedule"]


def test_async_invalid_input():
    with pytest.raises(ValueError):
        execute_function(async_mock_classify_email, invalid_email_json)


def test_async_missing_parameter():
    with pytest.raises(ValueError):
        execute_function(async_mock_classify_email, missing_param_json)


@pytest.mark.parametrize(
    "json_input, expected_exception",
    [
        (invalid_email_json, ValueError),
        (missing_param_json, ValueError),
        (
            {**valid_email_json, "extra_field": "value"},
            None,
        ),  # Extra fields should be ignored
    ],
)
def test_async_workflow_input_validation(json_input, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            execute_function(async_mock_classify_email, json_input)
    else:
        # Should not raise an exception
        execute_function(async_mock_classify_email, json_input)


@pytest.fixture
def async_sample_email():
    return Email(
        from_="fixture@example.com",
        to=["recipient@example.com"],
        cc=[],
        bcc=[],
        subject="Fixture Email",
        text_without_quote="This is a test email from a fixture.",
        created_at=datetime.now(),
    )


def test_async_with_fixture(async_sample_email):
    result = execute_function(async_mock_classify_email, {"email_message": async_sample_email.dict()})
    assert isinstance(result, EmailCategories)
    assert result.category == "Informative"
