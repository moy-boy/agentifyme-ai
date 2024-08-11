import traceback
from typing import List

import pytest
from pydantic import BaseModel

from agentifyme.workflows import WorkflowConfig, workflow


class CustomerQuery(BaseModel):
    customer_id: str
    query: str


class CustomerInfo(BaseModel):
    customer_id: str
    name: str
    email: str


class QueryCategory(BaseModel):
    category: str
    confidence: float


class Response(BaseModel):
    message: str


@workflow(name="get_customer_info", description="Retrieve customer information")
def get_customer_info(customer_id: str) -> CustomerInfo:
    # Dummy implementation for testing
    return CustomerInfo(
        customer_id=customer_id, name="John Doe", email="john@example.com"
    )


@workflow(name="categorize_query", description="Categorize customer query")
def categorize_query(query: str) -> QueryCategory:
    # Dummy implementation for testing
    return QueryCategory(category="billing", confidence=0.8)


@workflow(
    name="handle_customer_query",
    description="Handle customer query using nested workflows",
)
def handle_customer_query(customer_query: CustomerQuery) -> Response:
    try:
        customer_info = get_customer_info(customer_query.customer_id)
        query_category = categorize_query(customer_query.query)

        # Generate response based on customer info and query category
        response_message = f"Hello {customer_info.name}, we've received your {query_category.category} query and will respond shortly."
        return Response(message=response_message)
    except Exception as e:
        # print stack trace
        print(traceback.format_exc())
        raise e


def test_nested_workflow():
    workflow = WorkflowConfig._registry["handle_customer_query"]
    input_data = {
        "customer_query": {
            "customer_id": "12345",
            "query": "I have a question about my recent bill.",
        }
    }
    result = workflow(**input_data)

    assert isinstance(result, BaseModel)

    result_dict = result.model_dump()

    assert isinstance(result_dict, dict)
    assert "message" in result_dict
    assert "Hello John Doe" in result_dict["message"]
    assert "billing query" in result_dict["message"]


def test_nested_workflow_invalid_input():
    workflow = WorkflowConfig._registry["handle_customer_query"]
    with pytest.raises(ValueError):
        workflow.run(invalid_param="Some value")


def test_nested_workflow_missing_input():
    workflow = WorkflowConfig._registry["handle_customer_query"]
    with pytest.raises(ValueError):
        workflow.run()


def test_individual_workflows():
    customer_info_workflow = WorkflowConfig._registry["get_customer_info"]
    categorize_query_workflow = WorkflowConfig._registry["categorize_query"]

    customer_info_result = customer_info_workflow(customer_id="12345")
    assert isinstance(customer_info_result, CustomerInfo)
    assert customer_info_result.name == "John Doe"

    categorize_query_result = categorize_query_workflow.run(
        query="I have a billing question"
    )
    assert isinstance(categorize_query_result, QueryCategory)
    assert categorize_query_result.category == "billing"
