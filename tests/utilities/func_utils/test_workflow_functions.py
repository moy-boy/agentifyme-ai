from datetime import datetime
from typing import List

import pytest
from pydantic import BaseModel
from zoneinfo import ZoneInfo

from agentifyme.utilities.func_utils import (
    convert_json_to_args,
    execute_function,
)


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


def get_email_message(email_message: Email) -> str:
    """
    Get the email message.
    """
    return email_message.text_without_quote


def mock_classify_email(email_message: Email) -> EmailCategories:
    """
    Mock function to classify an email.
    """
    return EmailCategories(
        category="Informative",
        score=80,
        explanation="The email contains information about a meeting.",
        tags=["meeting", "schedule"],
    )


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


def test_email_message():
    result = execute_function(get_email_message, valid_email_json)
    assert isinstance(result, str)
    assert result == "Please attend the meeting tomorrow at 2 PM."


def test_valid_input():
    result = execute_function(mock_classify_email, valid_email_json)
    assert isinstance(result, EmailCategories)
    assert result.category == "Informative"
    assert result.score == 80
    assert result.explanation == "The email contains information about a meeting."
    assert result.tags == ["meeting", "schedule"]


def test_invalid_input():
    with pytest.raises(ValueError):
        execute_function(mock_classify_email, invalid_email_json)


def test_missing_parameter():
    with pytest.raises(ValueError):
        execute_function(mock_classify_email, missing_param_json)


def test_convert_json_to_args():
    args = convert_json_to_args(mock_classify_email, valid_email_json)
    assert "email_message" in args
    assert isinstance(args["email_message"], Email)
    assert args["email_message"].from_ == "sender@example.com"
    assert args["email_message"].to == ["recipient@example.com"]
    assert args["email_message"].subject == "Important Meeting"
    assert args["email_message"].created_at == datetime(2023, 8, 7, 10, 0, tzinfo=ZoneInfo("UTC"))


# Parameterized test example
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
def test_workflow_input_validation(json_input, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            execute_function(mock_classify_email, json_input)
    else:
        # Should not raise an exception
        execute_function(mock_classify_email, json_input)


# Fixture example
@pytest.fixture
def sample_email():
    return Email(
        from_="fixture@example.com",
        to=["recipient@example.com"],
        cc=[],
        bcc=[],
        subject="Fixture Email",
        text_without_quote="This is a test email from a fixture.",
        created_at=datetime.now(),
    )


def test_with_fixture(sample_email):
    result = mock_classify_email(sample_email)
    assert isinstance(result, EmailCategories)
    assert result.category == "Informative"
