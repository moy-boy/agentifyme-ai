# import asyncio
# from datetime import datetime
# from typing import List

# import pytest
# from pydantic import BaseModel

# from agentifyme.workflows import (
#     WorkflowConfig,
#     WorkflowExecutionError,
#     workflow,
# )


# class Email(BaseModel):
#     from_: str
#     to: List[str]
#     cc: List[str]
#     bcc: List[str]
#     subject: str
#     text_without_quote: str
#     created_at: datetime


# class EmailCategories(BaseModel):
#     category: str
#     confidence: float


# @workflow(
#     name="Classify email",
#     description="Classify given email into actionable, informative or irrelevant categories",
# )
# def classify_email(email_message: Email) -> EmailCategories:
#     # Dummy implementation for testing
#     return EmailCategories(category="actionable", confidence=0.9)


# @workflow(
#     name="Classify email async",
#     description="Asynchronously classify given email into actionable, informative or irrelevant categories",
# )
# async def classify_email_async(email_message: Email) -> EmailCategories:
#     # Dummy async implementation for testing
#     await asyncio.sleep(0.1)
#     return EmailCategories(category="actionable", confidence=0.9)


# @workflow(name="greet", description="Generate a greeting message.")
# def greet(name: str) -> str:
#     return f"Hello, {name}!"


# @workflow(name="greet_async", description="Asynchronously generate a greeting message.")
# async def greet_async(name: str) -> str:
#     await asyncio.sleep(0.1)
#     return f"Hello, {name}!"


# def test_simple_workflow():
#     _workflow = WorkflowConfig.get("greet")
#     result = _workflow(name="Alice")
#     assert result == "Hello, Alice!"


# @pytest.mark.asyncio
# async def test_simple_workflow_async():
#     _workflow = WorkflowConfig.get("greet_async")
#     result = await _workflow.arun(name="Alice")
#     assert result == "Hello, Alice!"


# def test_complex_workflow():
#     _workflow = WorkflowConfig.get("classify-email")
#     input_data = {
#         "email_message": Email(
#             from_="sender@example.com",
#             to=["recipient@example.com"],
#             cc=[],
#             bcc=[],
#             subject="Test Email",
#             text_without_quote="This is a test email.",
#             created_at=datetime(2023, 8, 6, 12, 0, 0),
#         )
#     }
#     result = _workflow(**input_data)
#     assert result.category == "actionable"
#     assert result.confidence == 0.9


# @pytest.mark.asyncio
# async def test_complex_workflow_async():
#     _workflow = WorkflowConfig.get("classify-email-async")
#     input_data = {
#         "email_message": Email(
#             from_="sender@example.com",
#             to=["recipient@example.com"],
#             cc=[],
#             bcc=[],
#             subject="Test Email",
#             text_without_quote="This is a test email.",
#             created_at=datetime(2023, 8, 6, 12, 0, 0),
#         )
#     }
#     result = await _workflow.arun(**input_data)
#     assert result.category == "actionable"
#     assert result.confidence == 0.9


# def test_invalid_input():
#     _workflow = WorkflowConfig.get("greet")
#     with pytest.raises(WorkflowExecutionError):
#         _workflow.run(invalid_param="Alice")


# @pytest.mark.asyncio
# async def test_invalid_input_async():
#     _workflow = WorkflowConfig.get("greet_async")
#     # with pytest.raises(AsyncWorkflowExecutionError):
#     #     await _workflow.arun(invalid_param="Alice")


# def test_missing_required_input():
#     _workflow = WorkflowConfig.get("greet")
#     with pytest.raises(WorkflowExecutionError):
#         _workflow.run()


# @pytest.mark.asyncio
# async def test_missing_required_input_async():
#     _workflow = WorkflowConfig.get("greet_async")
#     # with pytest.raises(AsyncWorkflowExecutionError):
#     #     await _workflow.arun()


# def test_extra_input_ignored():
#     _workflow = WorkflowConfig.get("greet")
#     result = _workflow.run(name="Bob", extra_param="Ignored")
#     assert result == "Hello, Bob!"


# @pytest.mark.asyncio
# async def test_extra_input_async():
#     _workflow = WorkflowConfig.get("greet_async")
#     # with pytest.raises(AsyncWorkflowExecutionError) as exc_info:
#     #     await _workflow.arun(name="Bob", extra_param="Ignored")
#     # assert "unexpected keyword argument 'extra_param'" in str(exc_info.value)
